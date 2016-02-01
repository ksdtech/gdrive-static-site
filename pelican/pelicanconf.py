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
IGNORE_FILES = ['_*.*', '*.x', '*.yml', '.#*']

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
# All other plugin code is in the gdrivepel module.

import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pelican import signals
from pelican.readers import HTMLReader
from gdrivepel.readers import MarkdownExtReader
from gdrivepel.generators import YamlGenerator, on_get_generators, on_all_generators_finalized

# File extensions that all generators will process.
READERS = { 'md': MarkdownExtReader, 'html': HTMLReader }

# Hook our generator logic in.
signals.get_generators.connect(on_get_generators)
signals.all_generators_finalized.connect(on_all_generators_finalized)
