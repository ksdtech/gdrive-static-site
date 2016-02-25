from __future__ import print_function

import logging
import os
import sys
import time

from bs4 import BeautifulSoup
import slate
from indextank.client import ApiClient

# logger for this file
logger = logging.getLogger(__name__)

class SearchIndexer:
  def __init__(self, index_name, source_root, api_url):
    self.index_name = index_name
    self.source_root = source_root
    self.root_len = len(source_root)
    self.api = ApiClient(api_url)
    index = None
    try:
      index = self.api.get_index(index_name)
      logger.debug('Found searchify index %s' % index_name)
    except:
      public_search_enabled = True
      logger.debug('Creating searchify index %s' % index_name)
      index = self.api.create_index(index_name, public_search_enabled)
      while not index.has_started():
        time.sleep(0.5)
      logger.debug('Searchify index %s started' % index_name)
    if index is None:
      logger.fatal('Could not create or get index %s' % index_name)
      sys.exit(1)

    self.index = index


  def _index_html(self, content, path):
    if content.content is None:
      logger.debug('skipping html index for %s - no content' % path)
      return

    # Available metadata: 'author', 'basename_raw', 'date',
    # 'email', 'exported_type', 'modified', 'relative_url',
    # 'slug', 'source_id', 'source_type', 'summary', 'template',
    # 'sorted_title', 'sort_priority', 'title', 'version' 
    title = content.metadata['title']
     # Works with UTC datetimes
    timestamp = int(time.mktime(content.metadata['modified'].timetuple()))

    # Remove all script and style elements
    soup = BeautifulSoup(content.content)
    for script in soup(['script', 'style']):
      script.extract()    
    text = soup.get_text()

    # TODO: variables = { 0: rating, 1: reputation, 2: visits }
    self.index.add_document(path, { 
      'text': text, 'title': title, 'timestamp' : timestamp })

  def _index_pdf(self, content, path):
    fpath = os.path.join(self.source_root, path)
    if not os.path.exists(fpath):
      logger.error('Indexer: Cannot read pdf at %s' % fpath)
      return

    # Available metadata: 'author', 'basename_raw', 'date',
    # 'email', 'exported_type', 'modified', 'relative_url',
    # 'slug', 'source_id', 'source_type', 'summary', 'template',
    # 'sorted_title', 'sort_priority', 'title', 'version' 
    title = content.metadata['title']
    # Works with UTC datetimes
    timestamp = int(time.mktime(content.metadata['modified'].timetuple()))

    with open(fpath) as f:
      doc = slate.PDF(f)
      i = 0
      for text in doc:
        i += 1

        # TODO: variables = { 0: rating, 1: reputation, 2: visits }
        self.index.add_document(path, { 
          'text': text, 'title': title, 'timestamp' : timestamp })

  def index_content(self, content):
    content_type = content.__class__.__name__
    source_path = content.source_path
    if source_path[:1] == '/':
      if source_path.startswith(self.source_root):
        source_path = source_path[self.root_len:]
      else:
        logger.debug('skipping out-of-path content %s, source %s' % (content_type, source_path))
        return

    if content_type == 'Article' or content_type == 'Page':
      self._index_html(content, source_path)
    elif content_type == 'Static':
      filename, extension = os.path.splitext(source_path)
      if extension == '.pdf':
        self._index_pdf(content, source_path)
      else:
        logger.debug('skipping unknown static type, source %s' % source_path)
    else:
      logger.debug('skipping unknown content %s, source %s' % (content_type, source_path))

def get_indexer(settings):
  if get_indexer.indexer is None:
    index_name = settings.get('SEARCHIFY_INDEX', settings.get('SUBSITE', 'main'))
    source_root = os.path.abspath(settings['PATH'])
    if source_root[-1:] != '/':
      source_root += '/'
    print('initializing indexer for %s with root %s' % (index_name, source_root))
    get_indexer.indexer = SearchIndexer(index_name, source_root, settings['SEARCHIFY_API_URL'])
  return get_indexer.indexer

get_indexer.indexer = None

def on_content(content):
  if content.settings.get('SEARCHIFY_API_URL'):
    get_indexer(content.settings).index_content(content)
