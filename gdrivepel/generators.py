from __future__ import print_function

import codecs
import logging
import os.path
import re
import sys
import yaml

from pelican.contents import is_valid_content
from pelican.generators import CachingGenerator, PagesGenerator
from pelican.readers import parse_path_metadata

from gdrivepel.contents import Page, DocMeta, NavMenu
from gdrivepel.readers import YamlReader
from gdrivepel.sanitizer import slugify, make_meta_filename
from gdrivepel.search import on_content

# logger for this file
logger = logging.getLogger(__name__)

class IllformedNavmenuError(Exception):
    pass

class IllformedSectionError(Exception):
    pass

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

YAML_GENERATOR_IGNORE_FILES = [ '_raw_*.*', '.#*', '_navmenu_auto_.yml', '.DS_Store' ]
YAML_METADATA_KEYS = [ 'author', 'basename_raw', 'date',
    'email', 'exported_type', 'modified', 'relative_url',
    'slug', 'source_id', 'source_type', 'summary', 'template',
    'sorted_title', 'sort_priority', 'title', 'version' ]
CONTENT_CLASSES = [ 'Doc', 'Page', 'Static', 'DocMeta', 'NavMenu' ]

# Example of Google doc href
# https://www.google.com/url
#   ?q=https://docs.google.com/document/d/1mZdFHJor-GGUiJd08F3wZb6pD-Aal7E3_4dqOWoTxWA/edit?usp%3Dsharing
#   &amp;sa=D&amp;ust=1455753241243000&amp;usg=AFQjCNF7OYw1X2o9Bkq4F8omptlyt8nPig

# Regex based on the one used in contents.py from pelican version 3.6.3
GDRIVE_LINK_RE = re.compile(
    r"""
    (?P<markup><\s*[^\>]*   # <a rel="nofollow" href=   --> markup
        (?:href|src|poster|data|cite|formaction|action)\s*=)
    (?P<quote>["\'])        # "                         --> quote
    (?:https\:\/\/www.google.com\/url\?q=https\:\/\/docs.google.com\/document\/d\/)
    (?P<docid>[-_a-zA-Z0-9]+) # Google doc id           --> docid
    (?:\/.+)                # rest of URL
    \2                      # "                         <-- quote
    """, re.X)


class YamlGenerator(CachingGenerator):
    """
    Process .yml files to merge metadata
    We will keep mappings of Google Doc ids to downloaded files, 
    navigation menus, section topics and subtopics here.

    We don't generate any output so we do not define a generate_output method.
    """

    def __init__(self, *args, **kwargs):
        super(YamlGenerator, self).__init__(*args, **kwargs)
        # Mapping from Google Doc id to URLs in the content/pages 
        # directory tree
        self.docid_map = { }
        self.by_classes = { }
        self.navmenus = { }
        self.index_pages = [ ]

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

        if hasattr(content, 'source_id'):
            if not content.source_id in self.docid_map:
                self.docid_map[content.source_id] = [ ]
            self.docid_map[content.source_id].append(content)

    def generate_context(self):
        # Only use YamlReader, don't ingore anything, but only read files with yml extension.
        self._patch_readers()

        # Custom settings for self.get_files
        saved_ignore_files = self.settings['IGNORE_FILES']
        self.settings['IGNORE_FILES'] = YAML_GENERATOR_IGNORE_FILES
        paths = self.settings.get('YAML_PATHS', self.settings['PAGE_PATHS'])
        filelist = self.get_files(paths, exclude=[], extensions=('yml'))
        self.settings['IGNORE_FILES'] = saved_ignore_files

        for f in filelist:
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

    def _doc_meta_for_page(self, location):
        dirname, fname = os.path.split(location)
        meta_filename = make_meta_filename(fname)
        yaml_filename = os.path.join(dirname, meta_filename)
        if yaml_filename in self.context['filenames']:
            doc_meta = self.context['filenames'][yaml_filename]
            return doc_meta
        return None

    def _folder_meta_for_page(self, location):
        """Work up the location hierarchy looking for a _folder_.yml DocMeta content"""
        # Location is something like pages/sites/district/general-information/lcap-and-accountability-reports/lcap-and-accountability-reports.md
        # See if we have a pages/sites/district/general-information/lcap-and-accountability-reports/_folder_.yml
        dirname = os.path.dirname(location)
        while dirname != '':
            yaml_filename = os.path.join(dirname, '_folder_.yml')
            if yaml_filename in self.context['filenames']:
                return self.context['filenames'][yaml_filename]
            dirname = os.path.dirname(dirname)
        return None

    def _add_yaml_meta_to_page(self, location, page):
        doc_meta = self._doc_meta_for_page(location)
        if doc_meta is not None:
            for key in YAML_METADATA_KEYS:
                val = doc_meta.metadata.get(key, None)
                if val is not None:
                    page.metadata[key] = val
            doc_meta.metadata.update({
                'content_class': page.__class__.__name__,
                'content_location': location })
            logger.debug('Updated meta for page %s' % location)
        else:
            logger.debug('No DocMeta for for page %s' % location)

        # Time to add our search indexes, too
        on_content(page)

    def _add_yaml_meta_to_pages(self):
        for location, page in self.by_classes['Doc'].iteritems():
            self._add_yaml_meta_to_page(location, page)

    def _href_for_location(self, location):
        return os.path.join(self.settings['SITEURL'], re.sub(r'^\/', '', location))

    def _get_submenu_for_section(self, folder, section_meta):
        submenu = [ ]
        l = len(section_meta.metadata['subtopics'])
        for t in section_meta.metadata['subtopics']:
            item = { 'title': t['title'] }
            item_type = 'link-local'
            sub_location = t['sub_folder']
            sub_folder, filename = os.path.split(sub_location)
            navmenu_file = os.path.join(sub_folder, '_navmenu_.yml')
            if navmenu_file in self.by_classes['NavMenu']:
                item_type = 'include'
            elif sub_location in self.by_classes['DocMeta']:
                section_meta = self.by_classes['DocMeta'][sub_location]
                subsub = self._get_submenu_for_section(sub_folder, section_meta)
                if len(subsub) > 0:
                    item_type = 'section'
                    item['submenu'] = subsub
            if item_type != 'include':
                item['href'] = t['location']
            item['type'] = item_type
            submenu.append(item)
        return submenu

    def _build_section_links(self, folder, section_meta):
        doc_links = [ ]
        for location, doc in self.by_classes['Doc'].iteritems():
            dirname, fname = os.path.split(location)
            if dirname == folder:
                title = None
                if 'title' in doc.metadata:
                    title = doc.metadata['title']
                else:
                    logger.warn('No title for %s %s in %s' % (doc.__class__.__name__, fname, dirname))
                    title = fname
                doc_links.append(
                    (doc.metadata.get('sorted_title', title), title, doc.url, doc.__class__.__name__))

        subfolder_links = [ ]
        for location, doc_meta in self.by_classes['DocMeta'].iteritems():
            dirname, fname = os.path.split(location)
            parent = os.path.dirname(dirname)
            if fname == '_folder_.yml' and parent == folder:
                title = None
                if 'title' in doc_meta.metadata:
                    title = doc_meta.metadata['title']
                else:
                    logger.warn('No title for subfolder %s in %s' % (dirname, parent))
                    title = fname
                subfolder_links.append(
                    (doc_meta.metadata.get('sorted_title', title), title, dirname, 'DocMeta'))

        section_meta.metadata['contents'] = [ ]
        for link in sorted(doc_links, key=lambda x: x[0]):
            location = link[2] # self._href_for_location(link[2])
            section_meta.metadata['contents'].append({ 
                'sorted_title': link[0],
                'title': link[1], 
                'location': location,
                'class': link[3] })

        section_meta.metadata['subtopics'] = [ ]
        for link in sorted(subfolder_links, key=lambda x: x[0]):
            location = link[2] # self._href_for_location(link[2])
            sub_location = os.path.join(link[2], '_folder_.yml')
            section_meta.metadata['subtopics'].append({ 
                'sorted_title': link[0],
                'title': link[1], 
                'location': location,
                'sub_folder': sub_location,
                'class': link[3] })

    def _create_section_index(self, folder, section_meta):
        page = None
        any_subtopics = len(section_meta.metadata['subtopics']) > 0
        first_doc = None
        for doc in section_meta.metadata['contents']:
            if doc['class'] == 'Page':
                first_doc = doc
                break

        content = None
        metadata = None
        if first_doc is not None:
            # Build an alias to the first document in the section
            # Use 'alias' template to generate the redirect in the
            # <head> element.
            metadata = {
                'template': 'alias',
                'slug': section_meta.metadata['slug'],
                'title': first_doc['title'],
                'redirect_url': first_doc['location']
            }

        elif any_subtopics:
            # Build an index page that just displays the submenus.
            content = '<p>Click on the links in the Contents area.<p>'
            metadata = {
                'template': 'section',
                'slug': section_meta.metadata['slug'],
                'title': section_meta.metadata['title']
            }

        else:
            # Build an index page at this location
            content = '<p>This section has no content.<p>'
            metadata = {
                'template': 'section',
                'slug': section_meta.metadata['slug'],
                'title': section_meta.metadata['title']
            }

        if metadata is not None:
            path = os.path.join(folder, 'index.html')
            metadata.update(parse_path_metadata(path, settings=self.settings))
            page = Page(content=content, metadata=metadata,
                             settings=self.settings, source_path=path,
                             context=self.context)
            self.add_source_path(page)
            self.index_pages.append(page)


    def _build_section_navmenu(self, folder, section_meta):
        submenu = self._get_submenu_for_section(folder, section_meta)
        section_meta.metadata['navmenu'] = submenu

    def _build_sections(self):
        # Build deepest sections first, because they may be included by shorter ones
        section_paths = sorted(self.by_classes['DocMeta'].keys(), key=lambda path: -len(path))
        for location in section_paths:
            dirname, fname = os.path.split(location)
            if fname == '_folder_.yml':
                section_meta = self.by_classes['DocMeta'][location]

                # Capture ordered links to contents and subtopics
                self._build_section_links(dirname, section_meta)

                # Depends on having subsection navmenus completed first
                self._build_section_navmenu(dirname, section_meta)

                # Must be done AFTER _build_section_links
                self._create_section_index(dirname, section_meta)

    def _set_sections_for_pages(self):
        """
        Set up the 'section' template and the 'section_links' for any
        page that is in a 'section'.
        """
        for location in self.by_classes['Page'].iterkeys():
            section_meta = self._folder_meta_for_page(location)
            if section_meta is not None:
                if 'contents' in section_meta.metadata:
                    page = self.context['filenames'][location]
                    page.template = 'section'
                    page.section_links = section_meta.metadata['contents']

    def _categorize_filenames(self):
        """
        Go through the global context's 'filenames' dict and create a new dict
        that has the content's class name ('Page', 'Static', 'DocMeta', etc) as
        the key.  Saves time when we want to find all Pages, etc.
        """
        for classname in CONTENT_CLASSES:
            self.by_classes[classname] = { }
        for location, obj in self.context['filenames'].iteritems():
            classname = None
            if obj is not None:
                classname = obj.__class__.__name__
                if classname in CONTENT_CLASSES:
                    self.by_classes[classname][location] = obj
                else:
                    logger.debug('Cannot categorize content item of class %s' % classname)

                # Pseudo-class for docs
                if classname in ['Page', 'Static']:
                    classname = 'Doc'
                    self.by_classes[classname][location] = obj

    def _resolve_navmenu_item(self, item, dirname):
        name = item['title']
        slug = slugify(name)
        link = item.get('href', None)
        submenu = [ ]
        item_type = item['type']
        if item_type == 'include':
            location = os.path.join(dirname, slug)
            if location not in self.navmenus:
                raise IllformedNavmenuError('cannot find included navmenu %s' % location)
            for (subname, sublink, subsub) in self.navmenus[location]:
                if link is None and sublink is not None:
                    link = sublink
                submenu.append((subname, sublink, subsub))
        elif 'submenu' in item:
            if item_type not in ['section', 'folder']:
                raise IllformedNavmenuError('submenu found for unknown type %s' % item_type)
            for subitem in item['submenu']:
                subdir = os.path.join(dirname, slug)
                subname, sublink, subsub = self._resolve_navmenu_item(subitem, subdir)
                if link is None and sublink is not None:
                    link = sublink
                submenu.append((subname, sublink, subsub))
        elif link is None:
            if item_type in ['link-local', 'link-external']:
                raise IllformedNavmenuError('link missing for %s type' % item_type) 
            elif item_type == 'doc':
                link = os.path.join(dirname, slug + '.html')
            elif item_type == 'pdf':
                link = os.path.join(dirname, slug + '.pdf')
        elif item_type not in ['link-local', 'link-external']:
                raise IllformedNavmenuError('link supplied for %s type' % item_type) 

        if link is None:
            link = '404.html?context=navmenu&slug=%s&dir=%s' % (slug, dirname)
        if not re.match(r'(http[s]?|ftp|mailto)\:', link):
            link = self._href_for_location(link)
        return (name, link, submenu)

    def _build_automenu(self):
        top = None

        # Get shortest paths first
        file_paths = sorted(self.by_classes['DocMeta'].keys(), key=lambda path: len(path))
        for location in file_paths:
            loc_parts = location.split(os.sep)
            depth = len(loc_parts) - 2
            if depth == 0 and loc_parts[0] == 'pages' and loc_parts[-1] == '_folder_.yml':
                folder_meta = self.by_classes['DocMeta'][location]
                navmenu = folder_meta.metadata['navmenu']
                if len(navmenu) > 0:
                    dirname, filename = os.path.split(location)
                    navmenu_file = os.path.abspath(os.path.join(self.path, 'pages', '_navmenu_auto_.yml'))
                    navmenu_dict = { 'navmenu': navmenu }
                    yaml_meta = yaml.safe_dump(navmenu_dict, default_flow_style=False,  explicit_start=True)
                    with codecs.open(navmenu_file, 'w+', 'utf-8') as f:
                        f.write(yaml_meta)
                    self.navmenus[dirname] = [ ]
                    for item in navmenu:
                        name, link, submenu = self._resolve_navmenu_item(item, dirname)
                        self.navmenus[dirname].append((name, link, submenu))
                    top = dirname
                break

        return top

    def _build_navmenus(self):
        top = None

        # Build deepest navmenus first, because they may be included by shorter ones
        navmenu_paths = sorted(self.by_classes['NavMenu'].keys(), key=lambda path: -len(path))
        for location in navmenu_paths:
            obj = self.by_classes['NavMenu'][location]
            dirname, filename = os.path.split(location)
            navmenu = obj.metadata['navmenu']
            self.navmenus[dirname] = [ ]
            for item in navmenu:
                name, link, submenu = self._resolve_navmenu_item(item, dirname)
                self.navmenus[dirname].append((name, link, submenu))
            top = dirname

        if self.settings.get('AUTOMENU', False):
            top = self._build_automenu()

        if top is not None:
            return self.navmenus[top]
        return [ ]

    def _find_closest_page_location_by_docid(self, location, docid):
        doc_metas = self.docid_map.get(docid, [])
        for doc_meta in doc_metas:
            if doc_meta.metadata.get('content_class') == 'Page':
                page_location = doc_meta.metadata.get('content_location')
                if page_location is not None and page_location in self.context['filenames']:
                    # print('Page %s found for docid %s' % (page_location, docid))
                    return page_location

        # print('No page found for docid %s' % docid)
        return None

    def _rewrite_gdrive_link_for_page(self, location, page):

        def replacer(m):
            docid = m.group('docid')
            closest_location = self._find_closest_page_location_by_docid(location, docid)

            if closest_location is not None:
                url = self._href_for_location(closest_location)
                return ''.join((m.group('markup'), m.group('quote'), url, m.group('quote')))
            else:
                # No substitution, just return original match
                return m.group(0)

        (content, subs_made) = GDRIVE_LINK_RE.subn(replacer, page._content)
        if subs_made > 0:
            # print('%s: mapped %d substitutions' % (location, subs_made))
            self.context['filenames'][location]._content = content
        else:
            # print('%s: NO substitutions' % location)
            pass


    def _rewrite_gdrive_links_for_pages(self):
        for location, page in self.by_classes['Page'].iteritems():
            self._rewrite_gdrive_link_for_page(location, page)

    def prepare_pages_for_output(self):
        """
        Add top-level navigation menu to all pages.
        Fix up templates and for pages in sections.
        Fix up links in pages that point to other Google Docs.
        """
        self._categorize_filenames()

        self._rewrite_gdrive_links_for_pages()
        self._add_yaml_meta_to_pages()
        
        self._build_sections()
        self._set_sections_for_pages()

        menuitems = self._build_navmenus()
        logger.debug('YamlGenerator menuitems %r' % menuitems)
        self.context.update( { 'MENUITEMS': menuitems } )

    def generate_output(self, writer):
        for page in self.index_pages:
            writer.write_file(
                page.save_as, self.get_template(page.template),
                self.context, page=page,
                relative_urls=self.settings['RELATIVE_URLS'],
                override_output=hasattr(page, 'override_save_as'))

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
    ygen = next(p for p in generators if p.__class__.__name__ == 'YamlGenerator')
    ygen.prepare_pages_for_output()
