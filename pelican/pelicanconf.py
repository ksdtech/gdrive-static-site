#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'webmaster@kentfieldschools.org'
SITENAME = u'Kentfield School District'
SITEURL = 'http://127.0.0.1:8088/ksd'

PATH = 'content'

# We have some static files here, too
STATIC_PATHS = ['pages']
STATIC_EXCLUDE_SOURCES = True

IGNORE_FILES = ['.#*', '.yml', '_*.*']

# Preserve pages file structure in output
PATH_METADATA= '(?P<path_no_ext>.*)\..*'
PAGE_SAVE_AS= '{path_no_ext}.html'
PAGE_URL= '{path_no_ext}.html'

TIMEZONE = 'America/Los_Angeles'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('Pelican', 'http://getpelican.com/'),
         ('Python.org', 'http://python.org/'),
         ('Jinja2', 'http://jinja.pocoo.org/'),
         ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('You can add links in your config file', '#'),
          ('Another social link', '#'),)

DEFAULT_PAGINATION = 10

LOAD_CONTENT_CACHE = False

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

import os.path
import re
import yaml

from markdown import Markdown
from markdown.inlinepatterns import Pattern
from markdown.util import etree

from pelican.readers import BaseReader
from pelican.utils import pelican_open


# ^snippet.html^
INCLUDE_HTML_RE = r'(\^)([^\^]+)\2'


class IncludeHtmlPattern(Pattern):
    """
    Return html read from a file specified as group(2)
    of the pattern.

    """
    def __init__(self, reader_instance):
        Pattern.__init__(self, INCLUDE_HTML_RE, reader_instance._md)
        self._reader_dir = os.path.dirname(reader_instance._source_path)

    def handleMatch(self, m):
        file_name = m.group(3)
        html_include_path = os.path.join(self._reader_dir, file_name)
        with pelican_open(html_include_path) as text:
            el = etree.fromstring(text)
            return el

class MarkdownExtReader(BaseReader):
    """Reader for Markdown files"""

    enabled = bool(Markdown)
    file_extensions = ['md', 'markdown', 'mkd', 'mdown']

    def __init__(self, *args, **kwargs):
        super(MarkdownExtReader, self).__init__(*args, **kwargs)
        self.extensions = list(self.settings['MD_EXTENSIONS'])

        if 'meta' not in self.extensions:
            self.extensions.append('meta')
        self._source_path = None

    def _parse_metadata_external(self):
        """Add external yaml metadata"""
        head, source_file =  os.path.split(self._source_path)
        meta_file = '_meta_' + source_file + '.yml'
        yaml_source_path = os.path.join(head, meta_file)
        if os.path.exists(yaml_source_path):
            with pelican_open(yaml_source_path) as text:
                d = yaml.load(text)
                # Set slug
                # if not 'slug' in d:
                #    d['slug'] = re.sub(r'', d['title'].tolower())
                # Now clean up dates
                for name, value in d.items():
                    d[name] = self.process_metadata(name, value)
                print "%s -> loaded %r" % (meta_file, d)
                return d
        print "%s -> NO METADATA" % meta_file
        return { }

    def _parse_metadata(self, meta):
        """Return the dict containing document metadata"""
        formatted_fields = self.settings['FORMATTED_FIELDS']

        # Add external yaml metadata first
        output = self._parse_metadata_external()

        # Now process inline metadata
        for name, value in meta.items():
            name = name.lower()
            if name in formatted_fields:
                # formatted metadata is special case and join all list values
                formatted_values = "\n".join(value)
                # reset the markdown instance to clear any state
                self._md.reset()
                formatted = self._md.convert(formatted_values)
                output[name] = self.process_metadata(name, formatted)
            elif name in METADATA_PROCESSORS:
                if len(value) > 1:
                    logger.warning(
                        'Duplicate definition of `%s` '
                        'for %s. Using first one.',
                        name, self._source_path)
                output[name] = self.process_metadata(name, value[0])
            elif len(value) > 1:
                # handle list metadata as list of string
                output[name] = self.process_metadata(name, value)
            else:
                # otherwise, handle metadata as single string
                output[name] = self.process_metadata(name, value[0])

        return output

    def read(self, source_path):
        """Parse content and metadata of markdown files"""

        self._source_path = source_path
        self._md = Markdown(extensions=self.extensions)

        # Custom handling of ^include.html^
        self._md.inlinePatterns['include_html'] = IncludeHtmlPattern(self)

        with pelican_open(source_path) as text:
            content = self._md.convert(text)

        metadata = self._parse_metadata(self._md.Meta)
        return content, metadata

READERS = { 'md': MarkdownExtReader }

