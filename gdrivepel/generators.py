import logging
import os.path
import sys

from pelican.contents import is_valid_content
from pelican.generators import CachingGenerator, PagesGenerator
from gdrivepel.contents import Page, DocMeta, NavMenu
from gdrivepel.readers import YamlReader

# logger for this file
logger = logging.getLogger(__name__)


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
        """Remove existing readers and rebuild just with YamlReader."""

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

    def add_source_path(self, content):
        """Record a source file path that a Generator found and processed.
        Store a reference to its Content object, for url lookups later.
        """
        super(YamlGenerator, self).add_source_path(content)
        logger.debug('YamlGenerator - add_source_path %s -> %s %s' % (content.source_id, content.dirname, content.basename))
        if not content.source_id in self.docid_map:
            self.docid_map[content.source_id] = [ ]
        self.docid_map[content.source_id].append(content)

    def generate_context(self):
        # Only use YamlReader, don't ingore anything, but only read files with yml extension.
        self._patch_readers()

        # God help us if they make this multi-threaded
        saved_ignore_files = self.settings['IGNORE_FILES']
        self.settings['IGNORE_FILES'] = [ ]
        for f in self.get_files(
                self.settings['PAGE_PATHS'], 
                exclude=[], extensions=('yml')):
            logger.debug('YamlGenerator - read %s' % f)

            # Define content class for _navmenu_.yml files.
            # YamlReader will also process these specially.
            content_class = DocMeta
            if os.path.basename(f) == '_navmenu_.yml':
              content_class = NavMenu

            doc_meta = self.get_cached_data(f, None)
            if doc_meta is None:
                try:
                    doc_meta = self.readers.read_file(
                        base_path=self.path, path=f, content_class=content_class,
                        context=self.context)
                except Exception as e:
                    logger.error('Could not process %s\n%s', f, e,
                        exc_info=self.settings.get('DEBUG', False))
                    self._add_failed_source_path(f)
                    continue

                if not is_valid_content(doc_meta, f):
                    self._add_failed_source_path(f)
                    continue

                self.cache_data(f, doc_meta)
                self.add_source_path(doc_meta)

        self.settings['IGNORE_FILES'] = saved_ignore_files

    # TODO: This code will go into the YamlGenerator which has the global
    # context of all files and folders downloaded from Google Drive.
    def _build_section_links(self, folder, doc_meta):
        doc_links = [ ]
        subfolder_links = [ ]
        for location, obj in self.context['filenames'].iteritems():
            dirname, fname = os.path.split(location)
            parent = os.path.dirname(dirname)
            if dirname == folder and obj is not None and isinstance(obj, Page):
                doc_links.append((obj.metadata['title'], location))
            elif fname == '_folder_.yml' and parent == folder:
                subfolder_links.append((obj.metadata['title'], dirname))

        doc_meta.metadata['contents'] = [ ]
        doc_meta.metadata['subtopics'] = [ ]
        count = 0
        for link in sorted(doc_links, key=lambda x: x[0]):
            doc_meta.metadata['contents'].append({ 'title': link[0], 'location': link[1] })
            count += 1
        for link in sorted(subfolder_links, key=lambda x: x[0]):
            doc_meta.metadata['subtopics'].append({ 'title': link[0], 'location': link[1] })
            count += 1

    def _add_yaml_meta_to_page(self, dirname, fname, page):
        yaml_doc = os.path.join(dirname, '_meta_' + fname + '.yml')
        if yaml_doc in self.context['filenames']:
            doc_meta = self.context['filenames'][yaml_doc]
            if doc_meta is not None:
                page.metadata.update(doc_meta.metadata)
                logger.debug('Updated meta for page %s/%s' % (dirname, fname))
            else:
                logger.debug('No DocMeta for for page %s/%s' % (dirname, fname))
                page.metadata['title'] = fname
                sys.exit(1)
        else:
            logger.debug('No meta file for page %s/%s' % (dirname, fname))
            page.metadata['title'] = fname

    def _add_yaml_meta_to_pages(self):
        # context['filenames'] is shared by all generators
        for location, obj in self.context['filenames'].iteritems():
            dirname, fname = os.path.split(location)
            if obj is not None and isinstance(obj, Page):
                self._add_yaml_meta_to_page(dirname, fname, obj)

    def _build_sections(self):
        # context['filenames'] is shared by all generators
        for location, obj in self.context['filenames'].iteritems():
            dirname, fname = os.path.split(location)
            if fname == '_folder_.yml' and  obj is not None and obj.__class__.__name__ == 'DocMeta':
                self._build_section_links(dirname, obj)

    # Do not define a generate_output method (yet)
    # def generate_output(self, writer):

    def _folder_meta_for_location(self, location):
        """Work up the location hierarchy looking for a _folder_.yml DocMeta content"""
        # Location is something like pages/sites/district/general-information/lcap-and-accountability-reports/lcap-and-accountability-reports.md
        # See if we have a pages/sites/district/general-information/lcap-and-accountability-reports/_folder_.yml
        dirname = os.path.dirname(location)
        print "checking %s " % dirname
        while dirname != '':
            yaml_doc = os.path.join(dirname, '_folder_.yml')
            if yaml_doc in self.context['filenames']:
                return self.context['filenames'][yaml_doc]
            dirname = os.path.dirname(dirname)
        return None

    def _page_in_section(self, location, page):
        meta = self._folder_meta_for_location(location)
        if meta is not None and meta.template == 'section':
            return meta
        return None
        # print "pgen %r " % pgen.pages
        # print "sgen %r " % sgen.staticfiles

    def _set_sections_for_pages(self):
        # context['filenames'] is shared by all generators
        for location, page in self.context['filenames'].iteritems():
            if page is not None and page.__class__.__name__ == 'Page':
                section_meta = self._page_in_section(location, page)
                if section_meta:
                    page.template = 'section'
                    doc_links = section_meta.metadata['contents']
                    if len(doc_links) > 0:
                        page.section_links = [(link['location'], link['title']) for link in doc_links]
                        logger.debug('page at %s -> section_links %r' % (location, page.section_links))

    def prepare_pages_for_output(self, pgen, sgen):
        """
        Add top-level navigation menu to all pages.
        Fix up templates and for pages in sections.
        Fix up links in pages that point to other Google Docs.
        """
        self._add_yaml_meta_to_pages()
        self._build_sections()
        self._set_sections_for_pages()


def on_get_generators(pelican):
    """
    Called when Pelican starts up, asking for generator classes from plugins.
    Add the YamlGenerator to the list of generators to use. Pelican will automatically 
    invoke PagesGenerator and StaticGenerator based on  settings values in the pelicanconf.py file.
    """
    return YamlGenerator

def on_all_generators_finalized(generators):
    """
    Called when all generators have set up contexts.
    We will build the navigation menus and specify section templates for pages in sections.
    """
    pgen = [p for p in generators if p.__class__.__name__ == 'PagesGenerator'][0]
    sgen = [p for p in generators if p.__class__.__name__ == 'StaticGenerator'][0]
    ygen = [p for p in generators if p.__class__.__name__ == 'YamlGenerator'][0]
    ygen.prepare_pages_for_output(pgen, sgen)

