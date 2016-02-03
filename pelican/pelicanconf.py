#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals
import os.path
import sys

AUTHOR = 'webmaster@kentfieldschools.org'
SITENAME = 'Kentfield School District'
SITEURL = 'http://127.0.0.1:8088/ksd'

# Base path for all source files
PATH = 'sites' # os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sites')

# Where to get articles (news / blog posts)
# ARTICLE_PATHS = []

# Directories to exclude from article search
# ARTICLE_EXCLUDES = []

# Where to get pages
PAGE_PATHS = [ 'district' ]

# Directories to exclude from page search
# PAGE_EXCLUDES = []

# Where to get static files (PDFs, images, etc.)
STATIC_PATHS = PAGE_PATHS

# Directories to exclude from static file search
# STATIC_EXCLUDES  = []

# If true, don't process articles and pages as static files
STATIC_EXCLUDE_SOURCES = True

# GLobal INGORE_FILES setting - overriden in YamlGenerator
IGNORE_FILES = ['_*.*', '*.yml', '.#*']

# Preserve pages file structure in output
PATH_METADATA= '(?P<path_no_ext>.*)\..*'
PAGE_SAVE_AS= '{path_no_ext}.html'
PAGE_URL= '{path_no_ext}.html'

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True

TIMEZONE = 'America/Los_Angeles'
DEFAULT_LANG = 'en'
THEME = 'themes/notmyidea'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# No menus in standard base template; We will build our own menu
DISPLAY_PAGES_ON_MENU = False
DISPLAY_CATEGORIES_ON_MENU = False

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

# Custom 'plugin' code for the gdrive-static-site project starts here.
# All other plugin code is in the gdrivepel module.

# Find patched bleach module
sys.path.append(os.path.join(os.path.dirname(__file__), '../../bleach'))
# Find gdrivepel module
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
