Jekyll-GDocs CMS Example
========================

Recursively copies files and folder from Google Drive. Also creates .yml metadata files with source information.

This project is adapted from the PyDrive-based downloader at:
https://github.com/Socialsquare/google-drive-migrator

1. Create a project in Google developer console.

2. Enable Drive API for the project.

3. Create Web consent screen for the project.

4. Create client secrets for the project.  Use redirect_uris: "http://localhost:8080/" and javascript_origins: "http://localhost:8080".  Download the client secrets JSON file to client_secrets.json file in top-level directory of this project.

5. Obtain the id of top level Google Drive folder to copy.

6. Install dependencies (PyDrive and html5lib):
```
pip install -r requirements.txt
```

7. Download files:
```
python copy_folder.py ~/Projects/_active/gdrive-static-site/hexo/source 0B93xtFAz_q1FYS04RFJfQkJkdGM
python copy_folder.py ~/Projects/_active/gdrive-static-site/pelican/content/pages 0B93xtFAz_q1FYS04RFJfQkJkdGM
```

8. Configure hexo. Edit site/_config.yml and site/themes/landscape/_config.yml.  Change url, root, and theme
menu links.

9. Generate site:
```
cd pelican
pelican -t ./themes/notmyidea ./content
```

10. Serve site/public folder:
```
emacs /usr/local/etc/apache2/2.4/httpd.conf
sudo /usr/local/Cellar/httpd24/2.4.12/bin/apachectl start
```
Some Ideas on Metadata and Site Organization
============================================

Website is organized from these types in Google Drive, organized in a folder tree:

- text/plain documents with titles ending in ".md" are downloaded and used as markdown source
- text/html documents with titles ending in ".html" are downloaded and used as html source
- application/vnd.google-apps.document documents are exported as text/html and used as html source
- application/pdf documents with titles ending in ".pdf" are donwloaded and used as static files
- text/plain documents with titles ending in ".yml" are downloaded and used for metdata

Any text/plain or application/vnd.google-apps.document Google Drive documents that have titles 
that begin with an underscore are treated as resource files. They are downloaded and may be used 
for inclusion (for example in iframes) but are not rendered as standalone pages.

Currently there are two types of manually maintained yaml files to be used in site construction.


_navmenu_.yml
--------------

Located in top level of each site. Used to build primary navigation.
navmenu is the top-level element. navmenu contains a list of submenus. 
Each submenu or item has a title and a type:

- parent - this is a parent menu, and has a submenu list
- link-local - this is a link to a URL on the same site
- link-external - this is a link to a URL on an external site
- pdf - this is a link to a downloadable PDF
- doc - this is a link to a page or article written in markdown. The name of the page content document is the menu item's title, plus the extension ".md"
- section - this is a link to a folder containing a _section_.yml file


_section_.yml
--------------

Located in a folder specified as a section in _navmenu_.yml.  Currently only
has one element:

- index_page - this is the title of the "overview" markdown page.  Normally it is omitted from the "contents"
section of the page, which is a secondary navigation menu built from the alphabetical titles
of any other pages in the folder.
