import codecs
import os
import re

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

def filter_span_class(name, value):
    bold_class = get_bold_class()
    print 'filter_span_class bold_class="%r", attr %s="%s"' % (bold_class, name, value)
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
    'img': ['src', 'alt'],
    'span': filter_span_class,
    'head': ['title'],
    'meta': ['content', 'http-equiv'],
}

def sanitize(content):
    styles = ''
    bold_class = set_bold_class(content)
    if bold_class:
        styles = '<style>.' + bold_class + '{font-weight:bold}</style>'
    i = content.index('<body')
    cleaned = clean(content[i:], 
        tags=MY_ALLOWED_TAGS, attributes=MY_ALLOWED_ATTRIBUTES,
        styles=[], strip=True, strip_comments=True)
    return styles + swap_entities(cleaned)

def sanitize_file(file_in, file_out):
    with codecs.open(file_in, 'r', 'utf-8') as f_in:
        file_content = f_in.read()
        sanitized_content = sanitize(file_content)
        with codecs.open(file_out, 'w+', 'utf-8') as f_out:
            f_out.write(sanitized_content)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run bleach on a source html file')
    parser.add_argument('file_name', metavar='FILE_NAME', help='html source file name')
    args = parser.parse_args()

    folder_name, file_name = os.path.split(args.file_name)
    to = os.path.join(folder_name, '_bleached_' + file_name)
    sanitize_file(args.file_name, to)

