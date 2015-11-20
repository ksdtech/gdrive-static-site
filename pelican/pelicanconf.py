#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'webmaster@kentfieldschools.org'
SITENAME = u'Kentfield School District'
SITEURL = 'http://127.0.0.1:8088/ksd'

PATH = 'content'

# We have some static files here, too
STATIC_PATHS = ['pages']
# STATIC_EXCLUDE_SOURCES = True

IGNORE_FILES = ['.#*', '.yml', '_*.*']

# Preserve pages file structure in output
PATH_METADATA= '(?P<path_no_ext>.*)\..*'
PAGE_SAVE_AS= '{path_no_ext}.html'
PAGE_URL= '{path_no_ext}.html'

TIMEZONE = 'America/Los_Angeles'

DEFAULT_LANG = u'en'

THEME = 'themes/notmyidea'

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

import fnmatch
import os
import os.path
import re
import yaml

from markdown import Markdown
from markdown.inlinepatterns import Pattern
from markdown.util import etree

from pelican.contents import Content, Page
from pelican.readers import BaseReader, MarkdownReader, HTMLReader
from pelican.utils import pelican_open

class Section(Page):
    def __init__(self, *args, **kwargs):
        super(Section, self).__init__(*args, **kwargs)
        self._output_location_referenced = False

    @property
    def url(self):
        # Note when url has been referenced, so we can avoid overriding it.
        self._output_location_referenced = True
        return super(Static, self).url

    @property
    def save_as(self):
        # Note when save_as has been referenced, so we can avoid overriding it.
        self._output_location_referenced = True
        return super(Static, self).save_as

    def attach_to(self, content):
        """Override our output directory with that of the given content object.
        """
        # Determine our file's new output path relative to the linking document.
        # If it currently lives beneath the linking document's source directory,
        # preserve that relationship on output. Otherwise, make it a sibling.
        linking_source_dir = os.path.dirname(content.source_path)
        tail_path = os.path.relpath(self.source_path, linking_source_dir)
        if tail_path.startswith(os.pardir + os.sep):
            tail_path = os.path.basename(tail_path)
        new_save_as = os.path.join(
            os.path.dirname(content.save_as), tail_path)

        # We do not build our new url by joining tail_path with the linking
        # document's url, because we cannot know just by looking at the latter
        # whether it points to the document itself or to its parent directory.
        # (An url like 'some/content' might mean a directory named 'some'
        # with a file named 'content', or it might mean a directory named
        # 'some/content' with a file named 'index.html'.) Rather than trying
        # to figure it out by comparing the linking document's url and save_as
        # path, we simply build our new url from our new save_as path.
        new_url = path_to_url(new_save_as)

        def _log_reason(reason):
            logger.warning("The {attach} link in %s cannot relocate %s "
                "because %s. Falling back to {filename} link behavior instead.",
                content.get_relative_source_path(),
                self.get_relative_source_path(), reason,
                extra={'limit_msg': "More {attach} warnings silenced."})

        # We never override an override, because we don't want to interfere
        # with user-defined overrides that might be in EXTRA_PATH_METADATA.
        if hasattr(self, 'override_save_as') or hasattr(self, 'override_url'):
            if new_save_as != self.save_as or new_url != self.url:
                _log_reason("its output location was already overridden")
            return

        # We never change an output path that has already been referenced,
        # because we don't want to break links that depend on that path.
        if self._output_location_referenced:
            if new_save_as != self.save_as or new_url != self.url:
                _log_reason("another link already referenced its location")
            return

        self.override_save_as = new_save_as
        self.override_url = new_url


# Inline include of an external html file.
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

class NavMenuReader(BaseReader):
    """Reader for _navmenu_.yml files"""

    enabled = False
    file_extensions = ['yml']

    def __init__(self, *args, **kwargs):
        super(NavMenuReader, self).__init__(*args, **kwargs)
        self._source_path = None

    def read(self, source_path):
        """Parse content and metadata of _navmenu_.yml files"""

        content = None
        metadata = dict()
        self._source_path = source_path
        source_file =  os.path.basename(source_path)
        if source_file == '_navmenu_.yml':
            with pelican_open(source_path) as text:
                metadata = yaml.load(text)
        else:
            raise Exception("Skipping %s" % source_file)
        return content, metadata

class MarkdownExtReader(MarkdownReader):
    """
    Extended reader for Markdown files. 
    Also reads metadata from yml files.
    And adds ^include.html^ pattern.
    """

    enabled = bool(Markdown)
    file_extensions = ['md', 'markdown', 'mkd', 'mdown']

    def __init__(self, *args, **kwargs):
        super(MarkdownExtReader, self).__init__(*args, **kwargs)

    def _build_section_links(self, metadata):
        section_links = [ ]
        dirname, section_file_name = os.path.split(self._source_path)
        meta_files = fnmatch.filter(os.listdir(dirname), '_meta_*.yml')
        for meta_file_name in meta_files:
            content_file_name = re.sub(r'(^_meta_|\.yml$)', '', meta_file_name)
            if content_file_name != section_file_name:
                yaml_source_path = os.path.join(dirname, meta_file_name)
                with pelican_open(yaml_source_path) as text:
                    info = yaml.load(text)
                    section_links.append((info['title'], info['relative_url']))
        return section_links

    def read(self, source_path):
        """Parse content and metadata of markdown files"""

        self._source_path = source_path
        self._md = Markdown(extensions=self.extensions)

        # Custom handling of ^include.html^
        self._md.inlinePatterns['include_html'] = IncludeHtmlPattern(self)

        with pelican_open(source_path) as text:
            content = self._md.convert(text)

        metadata = self._parse_metadata(self._md.Meta)
        if 'template' in metadata and metadata['template'] == 'section':
            metadata['section_links'] = self._build_section_links(metadata)

        return content, metadata

READERS = { 'md': MarkdownExtReader, 'yml': NavMenuReader, 
    'html': HTMLReader }

