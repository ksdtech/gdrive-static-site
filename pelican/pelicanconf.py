#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals
import os.path
import sys

AUTHOR = 'webmaster@kentfieldschools.org'

# These are commented out because we're using MULTISITE.
# See comments near bottom of this file.

# SITENAME = 'Kentfield School District'
# SITEURL = 'http://127.0.0.1:8088/ksd'

# Where to get articles (news / blog posts)
# ARTICLE_PATHS = []

# Directories to exclude from article search
# ARTICLE_EXCLUDES = []

# Where to get pages
# PAGE_PATHS = [ 'district' ]

# Directories to exclude from page search
# PAGE_EXCLUDES = []

# Where to get static files (PDFs, images, etc.)
# STATIC_PATHS = [ 'district' ]

# Directories to exclude from static file search
# STATIC_EXCLUDES  = []

# If true, don't process articles and pages as static files
STATIC_EXCLUDE_SOURCES = True

# GLobal INGORE_FILES setting - overriden in YamlGenerator
IGNORE_FILES = [ '_*.*', '*.yml', '.#*', '.DS_Store' ]

# Preserve pages file structure in output
# Extract 'path_no_ext' value from path (removing extension)
PATH_METADATA = '(?P<path_no_ext>.*)\..*'

# Pages in folders are not categorized
USE_FOLDER_AS_CATEGORY = False

# Use path_no_ext parsed from PATH_METADATA setting
PAGE_SAVE_AS = '{path_no_ext}.html'
PAGE_URL = '{path_no_ext}'

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

# Add our custom 'search' tempalate to Pelican's built-in ones
DIRECT_TEMPLATES = ['index', 'tags', 'categories', 'authors', 'archives', 'search']

DEFAULT_PAGINATION = 10
LOAD_CONTENT_CACHE = False

##########################################################################################
# Custom settings used by the gdrive-static-site project

# DocMeta content
# Use path_no_ext parsed from PATH_METADATA setting
DOCMETA_SAVE_AS = '{path_no_ext}.yml'

# If set to True, YamlGenerator will build top-level navigation system
AUTOMENU = True

# MULTISITE configuration (custom).
# If present and not an empty list, this is a multi-site installation.
# Otherwise it is a list of site prefix dictionaries
MULTISITE = {
  'district': {
    'PATH': 'sites/district',
    'SITENAME': 'Kentfield School District',
    'SITEURL': 'http://127.0.0.1:8088/ksd/district',
    'PAGE_PATHS': [ 'pages' ],
    'STATIC_PATHS': [ 'pages' ],
    'YAML_PATHS': [ 'pages' ],
    'OUTPUT_PATH': 'output/district',
    'SEARCHIFY_INDEX': 'district'
  },
  'bacich': {
    'PATH': 'sites/bacich',
    'SITENAME': 'Bacich Elementary School',
    'SITEURL': 'http://127.0.0.1:8088/ksd/bacich',
    'PAGE_PATHS': [ 'pages' ],
    'STATIC_PATHS': [ 'pages' ],
    'YAML_PATHS': [ 'pages' ],
    'OUTPUT_PATH': 'output/bacich',
    'SEARCHIFY_INDEX': 'bacich'
  },
  'kent': {
    'PATH': 'sites/kent',
    'SITENAME': 'Kent Middle School',
    'SITEURL': 'http://127.0.0.1:8088/ksd/kent',
    'PAGE_PATHS': [ 'pages' ],
    'STATIC_PATHS': [ 'pages' ],
    'YAML_PATHS': [ 'pages' ],
    'OUTPUT_PATH': 'output/kent',
    'SEARCHIFY_INDEX': 'kent'
  }
}

# API secrets
# You must define SEARCHIFY_API_URL and SEARCHIFY_PUBLIC_URL in the appconfig.py file
sys.path.append(os.path.dirname(__file__))
from appconfig import *

# Find gdrivepel module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import gdrivepel
PLUGINS = [ gdrivepel ]

# File extensions that all generators will process.
# Overriden in gdrivepel plugin, so no need to specify here.
# READERS = { 'md': gdrivepel.MarkdownExtReader, 'html': HTMLReader }

##########################################################################################
# Custom 'plugin' code for the gdrive-static-site project starts here.
# All other plugin code is in the gdrivepel module.

# If MULTISITE is set, you need to run the pelican executable once for 
# each site with a PELICAN_PATh environment variable set to the site's key
# in the MULTISITE setting. Example:
#
# PELICAN_SITE=district pelican -d -D -s pelican/pelicanconf.py -t pelican/themes/notmyidea 
#
if 'MULTISITE' in globals() and len(MULTISITE) > 0:
    SUBSITE = os.getenv('PELICAN_SITE', None)
    if SUBSITE is None:
        print('PELICAN_SITE environment variable (with value in %s) is required for MULITSITE configuration' % ', '.join(MULTISITE.keys()))
        sys.exit(2)
    else:
        for name, value in MULTISITE[SUBSITE].iteritems():
            globals()[name] = value
        print('MULTISITE for SUBSITE "%s"\n  PATH is "%s"\n  OUTPUT_PATH is "%s"' % (SUBSITE, PATH, OUTPUT_PATH))
