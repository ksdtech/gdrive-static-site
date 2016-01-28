#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'webmaster@kentfieldschools.org'
SITENAME = 'Kentfield School District'
SITEURL = 'http://127.0.0.1:8088/ksd'

PATH = 'content'

# We have some static files here, too
STATIC_PATHS = ['pages']
STATIC_EXCLUDE_SOURCES = True

# GLobal INGORE_FILES setting - overriden by YamlGenerator
IGNORE_FILES = ['_*.*', '*.yml', '.#*']

# Per-generator exclude path patterns
# ARTICLE_EXCLUDES = []
# PAGE_EXCLUDES    = []
# STATIC_EXCLUDES  = []

# Preserve pages file structure in output
PATH_METADATA= '(?P<path_no_ext>.*)\..*'
PAGE_SAVE_AS= '{path_no_ext}.html'
PAGE_URL= '{path_no_ext}.html'

TIMEZONE = 'America/Los_Angeles'

DEFAULT_LANG = 'en'

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
# RELATIVE_URLS = True

# Custom 'plugin' code for the gdrive-static-site project starts here.
import fnmatch
import logging
import os
import os.path
import re
import yaml

import dateutil.parser

from markdown import Markdown
from markdown.inlinepatterns import Pattern
from markdown.util import etree

from pelican import signals
from pelican.contents import Content, Page, is_valid_content
from pelican.generators import CachingGenerator
from pelican.readers import BaseReader, MarkdownReader, HTMLReader
from pelican.utils import pelican_open

# logger for this file
logger = logging.getLogger(__name__)

# Inline include of an external HTML file.
# Parses Markdown such as: ^snippet.html^
INCLUDE_HTML_RE = r'(\^)([^\^]+)\2'

class Section(Page):
    """A custom content type for a section page, that is a Page that 
    contains a table of contents (secondary navigation), listing documents 
    and subtopics within the page's folder."""

    def __init__(self, *args, **kwargs):
        super(Section, self).__init__(*args, **kwargs)
        self._output_location_referenced = False

    @property
    def url(self):
        # Note when url has been referenced, so we can avoid overriding it.
        self._output_location_referenced = True
        return super(Section, self).url

    @property
    def save_as(self):
        # Note when save_as has been referenced, so we can avoid overriding it.
        self._output_location_referenced = True
        return super(Section, self).save_as

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


class DocMeta(Content):
    """A custom content type for a YAML metadata file.  There are three types
    that we parse: _folder_.yml, _navmenu_.yml and _meta_xxxx.yml"""

    # Properties that gdrive-static-site copy_folder.py inserts or updates
    mandatory_properties = ('author','basename','dirname','relative_url','source_id',
        'source_type','title','slug','date','modified')
    # No output, so don't care
    default_template = 'page'

    # __init__(self, content, metadata, settings source_path, context)
    def __init__(self, *args, **kwargs):
        super(DocMeta, self).__init__(*args, **kwargs)
        logger.debug('DocMeta, source_path = %s' % self.source_path)
        logger.debug('      dirname = %s' % self.dirname)
        logger.debug('     basename = %s' % self.basename)
        logger.debug(' relative_url = %s' % self.relative_url)
        logger.debug('         slug = %s' % self.relative_url)


class IncludeHtmlPattern(Pattern):

    """
    Return the HTML element read from a file specified as group(2)
    of the INCLUDE_HTML_RE pattern.

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


class MarkdownExtReader(MarkdownReader):
    """
    Extended reader for Markdown files.  Also reads metadata from associated
    yml files. And adds the ^include.html^ pattern from the IncludeHtmlPattern
    class.
    """

    enabled = bool(Markdown)
    file_extensions = ['md', 'markdown', 'mkd', 'mdown']

    def __init__(self, *args, **kwargs):
        super(MarkdownExtReader, self).__init__(*args, **kwargs)

    # TODO: This code will go into the YamlGenerator which has the global
    # context of all files and folders downloaded from Google Drive.
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
        """Parse content and metadata of markdown files."""

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


class YamlReader(BaseReader):
    """Reader for _folder_.yml and _navmenu_.yml files"""

    enabled = True
    file_extensions = ['yaml', 'yml']

    def __init__(self, *args, **kwargs):
        super(YamlReader, self).__init__(*args, **kwargs)
        self._source_path = None

    def read(self, source_path):
        """Parse content and metadata of .yml files"""

        content = None
        metadata = dict()
        self._source_path = source_path
        source_file =  os.path.basename(source_path)
        with pelican_open(source_path) as text:
            metadata = yaml.load(text)
        for key in ['date', 'modified']:
            metadata[key] = dateutil.parser.parse(metadata[key])
        return content, metadata


# Global READERS setting - overriden by YamlGenerator
READERS = { 'md': MarkdownExtReader, 'html': HTMLReader }


class YamlGenerator(CachingGenerator):
    """
    Process .yml files to merge metadata
    We will keep mappings of Google Doc ids to downloaded files, 
    navigation menus, section topics and subtopics here.

    We don't generate any output!
    """

    def __init__(self, *args, **kwargs):
        super(YamlGenerator, self).__init__(*args, **kwargs)
        # Mapping from Google Doc id to URLs in the content/pages 
        # directory tree
        self.docid_map = { }

    def _patch_readers(self):
        # Remove existing readers and rebuild just with YamlReader
        self.readers.readers = {}
        self.readers.reader_classes = {}

        for cls in [YamlReader]:
            if not cls.enabled:
                logger.debug('Missing dependencies for %s',
                             ', '.join(cls.file_extensions))
                continue

            for ext in cls.file_extensions:
                self.readers.reader_classes[ext] = cls

        for fmt, reader_class in self.readers.reader_classes.items():
            if not reader_class:
                continue

            self.readers.readers[fmt] = reader_class(self.readers.settings)


    def generate_context(self):
        # Only use YamlReader, don't ingore anything, but only read files with yml extension.
        self._patch_readers()
        self.settings['IGNORE_FILES'] = []
        for f in self.get_files(
                self.settings['PAGE_PATHS'], 
                exclude=[], extensions=('yml')):
            logger.debug('YamlGenerator - read %s' % f)
            doc_meta = self.get_cached_data(f, None)
            if doc_meta is None:
                try:
                    doc_meta = self.readers.read_file(
                        base_path=self.path, path=f, content_class=DocMeta,
                        context=self.context)
                except Exception as e:
                    logger.error('Could not process %s\n%s', f, e,
                        exc_info=self.settings.get('DEBUG', False))
                    self._add_failed_source_path(f)
                    continue

                if not is_valid_content(doc_meta, f):
                    self._add_failed_source_path(f)
                    continue

    # No generate_output method




# Here are the settings that we can read in the readers object.
# We set the 'yaml_only_reader' setting in the YamlGenerator instance
# so that we can detect it in the readers_init signal.
"""
{
 'ARTICLE_EXCLUDES': ['pages'],
 'ARTICLE_LANG_SAVE_AS': '{slug}-{lang}.html',
 'ARTICLE_LANG_URL': '{slug}-{lang}.html',
 'ARTICLE_ORDER_BY': 'reversed-date',
 'ARTICLE_PATHS': [''],
 'ARTICLE_PERMALINK_STRUCTURE': '',
 'ARTICLE_SAVE_AS': '{slug}.html',
 'ARTICLE_URL': '{slug}.html',
 'AUTHOR': 'webmaster@kentfieldschools.org',
 'AUTHOR_FEED_ATOM': None,
 'AUTHOR_FEED_RSS': None,
 'AUTHOR_SAVE_AS': 'author/{slug}.html',
 'AUTHOR_URL': 'author/{slug}.html',
 'CACHE_CONTENT': False,
 'CACHE_PATH': '/Users/pz/Projects/_active/gdrive-static-site/pelican/cache',
 'CATEGORY_FEED_ATOM': None,
 'CATEGORY_SAVE_AS': 'category/{slug}.html',
 'CATEGORY_URL': 'category/{slug}.html',
 'CHECK_MODIFIED_METHOD': 'mtime',
 'CONTENT_CACHING_LAYER': 'reader',
 'CSS_FILE': 'main.css',
 'DATE_FORMATS': {},
 'DAY_ARCHIVE_SAVE_AS': '',
 'DEBUG': True,
 'DEFAULT_CATEGORY': 'misc',
 'DEFAULT_DATE_FORMAT': '%a %d %B %Y',
 'DEFAULT_LANG': 'en',
 'DEFAULT_METADATA': {},
 'DEFAULT_ORPHANS': 0,
 'DEFAULT_PAGINATION': 10,
 'DEFAULT_STATUS': 'published'
 'DELETE_OUTPUT_DIRECTORY': True,
 'DIRECT_TEMPLATES': ['index', 'tags', 'categories', 'authors', 'archives'],
 'DISPLAY_CATEGORIES_ON_MEN': True,
 'DISPLAY_PAGES_ON_MEN': True,
 'DOCUTILS_SETTINGS': {},
 'DRAFT_LANG_SAVE_AS': 'drafts/{slug}-{lang}.html',
 'DRAFT_LANG_URL': 'drafts/{slug}-{lang}.html',
 'DRAFT_SAVE_AS': 'drafts/{slug}.html',
 'DRAFT_URL': 'drafts/{slug}.html',
 'EXTRA_PATH_METADATA': {},
 'EXTRA_TEMPLATES_PATHS': [],
 'FEED_ALL_ATOM': None,
 'FEED_DOMAIN': 'http://127.0.0.1:8088/ksd',
 'FEED_MAX_ITEMS': '',
 'FILENAME_METADATA': '(?P<date>\\d{4}-\\d{2}-\\d{2}).*',
 'FORMATTED_FIELDS': ['summary'],
 'GZIP_CACHE': True,
 'IGNORE_FILES': ['.#*', '.yml', '_*.*'],
 'INCLUDE_HTML_RE': '(\\^)([^\\^]+)\\2',
 'INTRASITE_LINK_REGEX': '[{|](?P<what>.*?)[|}]',
 'JINJA_EXTENSIONS': [],
 'JINJA_FILTERS': {},
 'LINKS': (
    ('Pelican', 'http://getpelican.com/'),
    ('Jinja2', 'http://jinja.pocoo.org/'),
    ('Python.org', 'http://python.org/'),
    ('You can modify those links in your config file', '#')),
 'LOAD_CONTENT_CACHE': False,
 'LOCALE': [''],
 'LOG_FILTER': [],
 'MD_EXTENSIONS': ['codehilite(css_class=highlight)', 'extra'],
 'MONTH_ARCHIVE_SAVE_AS': '',
 'NEWEST_FIRST_ARCHIVES': True,
 'OUTPUT_PATH': '/Users/pz/Projects/_active/gdrive-static-site/pelican/output', 
 'OUTPUT_RETENTION': [],
 'OUTPUT_SOURCES': False,
 'OUTPUT_SOURCES_EXTENSION': '.text',
 'PAGE_EXCLUDES': [''],
 'PAGE_LANG_SAVE_AS': 'pages/{slug}-{lang}.html',
 'PAGE_LANG_URL': 'pages/{slug}-{lang}.html',
 'PAGE_ORDER_BY': 'basename', 'WITH_FUTURE_DATES': True,
 'PAGE_PATHS': ['pages'],
 'PAGE_SAVE_AS': '{path_no_ext}.html',
 'PAGE_URL': '{path_no_ext}.html',
 'PAGINATED_DIRECT_TEMPLATES': ['index'],
 'PAGINATION_PATTERNS': [PaginationRule(min_page=0, URL='{name}{number}{extension}', SAVE_AS='{name}{number}{extension}')],
 'PATH': '/Users/pz/Projects/_active/gdrive-static-site/pelican/content',
 'PATH_METADATA': '(?P<path_no_ext>.*)\\..*',
 'PELICAN_CLASS': 'pelican.Pelican',
 'PLUGINS': [],
 'PLUGIN_PATHS': [],
 'PYGMENTS_RST_OPTIONS': {},
 'READERS': {
    'md': <class 'pelicanconf.MarkdownExtReader'>,
    'html': <class 'pelican.readers.HTMLReader'>},
 'RELATIVE_URLS': False,
 'REVERSE_CATEGORY_ORDER': False,
 'SITENAME': 'Kentfield School District',
 'SITEURL': 'http://127.0.0.1:8088/ksd',
 'SLUGIFY_SOURCE': 'title',
 'SLUG_SUBSTITUTIONS': (),
 'SOCIAL': (
    ('You can add links in your config file', '#'),
    ('Another social link','#')),
 'STATIC_EXCLUDES': [],
 'STATIC_EXCLUDE_SOURCES': True,
 'STATIC_PATHS': ['pages'],
 'STATIC_SAVE_AS': '{path}',
 'STATIC_URL': '{path}',
 'SUMMARY_MAX_LENGTH': 50,
 'TAG_SAVE_AS': 'tag/{slug}.html',
 'TAG_URL': 'tag/{slug}.html',
 'TEMPLATE_PAGES': {},
 'THEME': '/Users/pz/Projects/_active/gdrive-static-site/pelican/themes/notmyidea',
 'THEME_STATIC_DIR': 'theme',
 'THEME_STATIC_PATHS': ['static'],
 'TIMEZONE': 'America/Los_Angeles',
 'TRANSLATION_FEED_ATOM': None,
 'TYPOGRIFY': False,
 'TYPOGRIFY_IGNORE_TAGS': [],
 'USE_FOLDER_AS_CATEGORY': True,
 'WRITE_SELECTED': [],
 'YEAR_ARCHIVE_SAVE_AS': '',
 'yaml_only_reader': True,
}
"""


def on_get_generators(pelican_obj):
    """Called when Pelican starts up, asking for generator classes from plugins."""
    return YamlGenerator

signals.get_generators.connect(on_get_generators)

