import cgi
import codecs
import os
import re
import sys
import yaml

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../bleach'))
from bleach import clean

# mozilla/bleach and or html5lib tokenizer/sanitizer still have some bugs
# 1.  <html><head><style> doesn't seem to be stripped
# 2.  html entities are messed up. See https://github.com/mozilla/bleach/issues/143
# 3.  Find some way to remove "empty" elements, such as: <a></a>, <li></li>, <p></p> etc.
# 4.  Remove <span> tag if "class" attribute was filtered out

ENTITY_REPLACEMENTS = {
    '\xa0': '&nbsp;'
}

def swap_entities(text):
    for k, v in ENTITY_REPLACEMENTS.items():
        text = re.sub(k, v, text)
    return text

# Look for the style that represents "<strong>"
bold_class = None

def get_bold_class():
    global bold_class
    return bold_class

# .c3{font-weight:bold}
def set_bold_class(content):
    global bold_class
    m = re.search(r'\.(c\d+)\{font-weight:bold\}', content)
    if m:
        bold_class = m.group(1)
    else:
        bold_class = None
    return bold_class

# TODO: change style width: and height: to attributes
def img_attributes(name, value):
    if name in ['src', 'alt', 'style']:
        return True
    return False

# TODO: change <span> with bold class to <strong>
def span_attributes(name, value):
    bold_class = get_bold_class()
    # print 'filter_span_class bold_class="%r", attr %s="%s"' % (bold_class, name, value)
    if bold_class is not None and name == 'class' and value == bold_class:
        return True
    return False

MY_ALLOWED_TAGS = [
    'a',
    'abbr',
    'acronym',
    'b',
    'blockquote',
    'code',
    'em',
    'i',
    'li',
    'ol',
    'strong',
    'ul',
    'p',
    'span',
    'table',
    'tbody',
    'tr',
    'th',
    'td',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'img'
]

MY_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'abbr': ['title'],
    'acronym': ['title'],
    'head': ['title'],
    'meta': ['content', 'http-equiv'],
    'img': ['src', 'alt', 'style'],
    'span': span_attributes
}

MY_ALLOWED_STYLES = [
    'width', 'height'
]

def head(metadata):
    title = metadata.pop('title', 'TITLE')
    metadata.pop('dirname', None)
    head_lines = [ '<head>', 
        '<meta name="charset" content="utf-8">', 
        '<title>%s</title>' % cgi.escape(title) ]
    for name, content in metadata.iteritems():
        if content:
            head_lines.append('<meta name="%s" content="%s">' % (name, cgi.escape(content)))
    head_lines.append('</head>')
    return '\n'.join(head_lines)

def sanitize(content, metadata):
    # parse content looking for the span class that signifies "bold"
    styles = [ ]
    bold_class = set_bold_class(content)
    if bold_class:
        styles = [ '<style>.' + bold_class + '{font-weight:bold}</style>' ]

    # parse body of html
    i = content.index('<body')
    body = clean(content[i:], 
        tags=MY_ALLOWED_TAGS, attributes=MY_ALLOWED_ATTRIBUTES,
        styles=MY_ALLOWED_STYLES, strip=True, strip_comments=True)

    # build a complete html5 document with title, meta elements and bold style
    html = '<!doctype html>\n<html>\n'
    html += head(metadata)
    html += '<body>\n'
    html += '\n'.join(styles)
    html += swap_entities(body)
    html += '</body>\n</html>\n'
    return html

def sanitize_html_file(file_in, file_out, metadata):
    with codecs.open(file_in, 'r', 'utf-8') as f_in:
        file_content = f_in.read()
        sanitized_content = sanitize(file_content, metadata)
        with codecs.open(file_out, 'w+', 'utf-8') as f_out:
            f_out.write(sanitized_content)

def prepend_markdown_metadata(file_in, file_out, metadata):
    metadata.pop('dirname', None)
    with codecs.open(file_in, 'r', 'utf-8') as f_in:
        file_content = f_in.read()
        with codecs.open(file_out, 'w+', 'utf-8') as f_out:
            add_blank_line = False
            for name, content in metadata.iteritems():
                if content:
                    f_out.write('%s: %s\n' % (name.capitalize(), content))
                    add_blank_line = True
            i = file_content.index('\n')
            test = file_content[:i]
            if add_blank_line and not re.match(r'^([^:]+):\s+(.+)$', test):
                f_out.write('\n')
            f_out.write(file_content.lstrip())

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run bleach on a source html file')
    parser.add_argument('file_name', metavar='FILE_NAME', help='html target file name')
    args = parser.parse_args()

    dirname, basename = os.path.split(args.file_name)
    file_from = os.path.join(dirname, '_raw_' + basename)
    file_to = os.path.join(dirname, basename)
    meta_name = '_meta_' + basename + '.yml'
    metadata = yaml.load(codecs.open(os.path.join(dirname, meta_name), 'r', 'utf-8'))
    sanitize_html_file(file_from, file_to, metadata)

