
import fnmatch
import logging
import os.path
import re
import yaml

import dateutil.parser

from markdown import Markdown
from markdown.inlinepatterns import Pattern
from markdown.util import etree

from pelican.readers import BaseReader, MarkdownReader
from pelican.utils import pelican_open

# logger for this file
logger = logging.getLogger(__name__)

# Inline include of an external HTML file.
# Parses Markdown such as: ^snippet.html^
INCLUDE_HTML_RE = r'(\^)([^\^]+)\2'

class IncludeHtmlPattern(Pattern):

    """
    Return the HTML element read from a file specified as group(2)
    of the INCLUDE_HTML_RE pattern.

    """
    def __init__(self, reader_instance):
        Pattern.__init__(self, INCLUDE_HTML_RE, reader_instance._md)
        self._reader_dir = os.path.dirname(reader_instance._source_path)

    def handleMatch(self, m):
        # Prepend '_' if not specified in include
        include_fname = m.group(3)
        if include_fname[:1] != '_':
            include_fname = '_' + include_fname
        include_path = os.path.join(self._reader_dir, include_fname)
        with pelican_open(include_path) as text:
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

    def read(self, source_path):
        """Parse content and metadata of markdown files."""

        self._source_path = source_path
        self._md = Markdown(extensions=self.extensions)

        # Custom handling of ^include.html^
        self._md.inlinePatterns['include_html'] = IncludeHtmlPattern(self)

        with pelican_open(source_path) as text:
            content = self._md.convert(text)

        metadata = self._parse_metadata(self._md.Meta)
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
        with pelican_open(source_path) as text:
            metadata = yaml.load(text)
        fname = os.path.basename(source_path)

        # Special processing for _navmenu_.yml files
        if fname == '_navmenu_.yml':
            # Read selected gdrive metadata 
            meta_navmenu_path = os.path.join(os.path.dirname(source_path), '_meta__navmenu_.yml.yml')
            with pelican_open(meta_navmenu_path) as meta:
                gdrive_meta = yaml.load(meta)
                for key in [ 'author', 'basename', 'date', 'dirname', 'email', 'modified',
                    'source_id', 'source_type', 'version' ]:
                    metadata[key] = gdrive_meta[key]

        for key in ['date', 'modified']:
            metadata[key] = dateutil.parser.parse(metadata[key])
        return content, metadata
