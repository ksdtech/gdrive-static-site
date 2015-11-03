Jekyll-GDocs CMS Example
========================

Recursively copies files and folder from Google Drive. Also creates .yaml metadata files with source information.

This project is adapted from the PyDrive-based downloader at:
https://github.com/Socialsquare/google-drive-migrator

1. Create a project in Google developer console.
2. Enable Drive API for the project.
3. Create Web consent screen for the project.
4. Create client secrets for the project.  Use redirect_uris: "http://localhost:8080/" and javascript_origins: "http://localhost:8080".  Download the client secrets JSON file to client_secrets.json file in top-level directory of this project.
5. Obtain the id of top level Google Drive folder to copy.
6. python copy_folder.py /path/to/download/folder google_drive_folder_id

```
python copy_folder.py /Users/pz/Projects/_active/gdrive-static-site/project 0B93xtFAz_q1FYS04RFJfQkJkdGM
```

Some Ideas on Metadata and Site Organization
============================================

Manually maintained yaml files to be used in site construction

navmenu__.yaml
--------------

Located in top level of each site. Used to build primary navigation.
navmenu is the top-level element. navmenu contains a list of submenus. 
Each submenu or item has a title and a type:

- parent - this is a parent menu, and has a submenu list
- link-local - this is a link to a URL on the same site
- link-external - this is a link to a URL on an external site
- pdf - this is a link to a downloadable PDF
- doc - this is a link to a page or article written in markdown. The name of the page content document is the menu item's title, plus the extension ".md"
- section - this is a link to a folder containing a section__.yaml file

section__.yaml
--------------

Located in a folder specified as a section in navmenu__.yaml.  Currently only
has one element:

- index_page - this is the title of the "overview" markdown page.  Normally it is omitted from the "contents"
section of the page, which is a secondary navigation menu built from the alphabetical titles
of any other pages in the folder.
