gdrive-static-site
==================
Generate a static website from Google Drive folders and docs.

There are two processes involved:

1. The copy\_folder.py script recursively downloads folders and docs
to a local directory tree from Google Drive using the Google Drive API, parsing and building metadata
and sanitizing the exported HTML from Google Docs.

2. The Pelican Python static website generator processes the local tree to output the finished
website.  Special templates are invoked to create "sections" and primary and secondary navigation.


copy\_folder.py
---------------
Recursively copies files and folder from Google Drive. Also creates .yml metadata files with source information.

This project is adapted from the PyDrive-based downloader at:
https://github.com/Socialsquare/google-drive-migrator

1. Create a project in Google developer console.

2. Enable Drive API for the project.

3. Create Web consent screen for the project.

4. Create client secrets for the project.  Use redirect\_uris: "http://localhost:8080/" and javascript_origins: "http://localhost:8080".  Download the client secrets JSON file to client\_secrets.json file in top-level directory of this project.

5. Obtain the id of top level Google Drive folder to copy.

6. Install dependencies (PyDrive and html5lib):

        pip install -r requirements.txt

7. Download and post-process files. copy\_folder takes two arguments: The Google Drive item id 
of the top-level folder to start downloading with, and a path to download that folder to 
(a folder with the "slugified" name of the Google Drive folder will be created within
the target folder).  Then Pelican will process files within the target as static pages
underneath the parent folder. 

As an example, let's say the Google Drive folder with id "0B93xtFAz_q1FQmdILTVtcGRIZlk" is named
"Sites". Then we execute this command:

        python copy_folder.py 0B93xtFAz_q1FQmdILTVtcGRIZlk pelican

And we will end up with a "sites" folder inside the "pelican" folder.  Hint: don't use 
"output" as the target folder name. For the following discussion let's assume we end
up with this directory tree on our local disk:

        gdrive-static-site/
            pelican/
                pelicanconf.py
                sites/
                    district/
                         pages/
                             about-our-district.md
                             district-logo.png
                    bacich/
                         pages/
                             about-bacich-school.md
                             bacich-logo.png
                    kent/
                         pages/
                             about-kent-school.md
                             kent-logo.png
                output/
                     ... pelican will place output here ...


Pelican Configuration
---------------------
1. Configure Pelican. Edit pelican/pelicanconf.py, setting the PATH variable 
relative to the  "pelican" directory (or to an absolute path). See Pelican docs 
for more information. Example:

        AUTHOR = u'webmaster@kentfieldschools.org'
        SITENAME = u'Kentfield School District'
        SITEURL = 'http://127.0.0.1:8088/ksd'

        PATH = 'sites'

        # We will look for .html and .md files here
        PAGE_PATHS = [ 'district', 'bacich', 'kent' ]

        # We have some static files here, too
        STATIC_PATHS = PAGE_PATHS
        STATIC_EXCLUDE_SOURCES = True

        IGNORE_FILES = ['.#*', '.yml', '_*.*']

2. Edit pelican/publishconf.py if necessary. See Pelican docs for more information.

3. Edit the theme you will use (we are testing with the "notmyidea" theme). 
See Pelican docs for more information.

4. Generate the site:

        pelican pelican/sites -d -s pelican/pelicanconf.py -t pelican/themes/notmyidea 

'-D' flag is for debug output
'-d' flag is to delete the output directory first

5. Serve the pelican/output folder (see Pelican docs for how to change this):

        emacs /usr/local/etc/apache2/2.4/httpd.conf
        sudo /usr/local/Cellar/httpd24/2.4.12/bin/apachectl start


Download Processor and Metadata Description
===========================================
Here is the way the download processor handles different Google Drive
folder and document types.


Titles
------
Every Google Drive item (folder or document) has a title or name.
These can contain any unicode character but should avoid the characters
"/" or ":".  The titles of native
Google Docs should not end in a file extension like ".html".
The titles of "text" documents such as YAML, HTML, or Markdown
documents should have a file extension at the end of the title 
(.yml", ".html", or ".md" respectively). Other non-native documents
with recognizable file types (images, PDFs and the like)
should also have a file extension (so that if they are downloaded
the file extension will be set for the downloaded file on the user's system.)

Items with titles that begin with special prefixes are handled specially.

An underscore "\_" prefix indicates that the document will be downloaded
for use by the Pelican processor, but will not stand on its own as a 
list web page or folder.

Two decimal digit "0-9" characters followed by a right bracket "]" character 
and 1 or more optional space " " characters will be stripped off when
creating the item's slug (web page URL) and title.  The two-digit prefix
can be used to order items in a "section" template or navigation menu
(see below).  Note that if a Google Drive document is located in more
than one Drive folder (Drive folders are really just tags), the name
will be the same in both locations.  For this reason, thhere is another 
way to override the ordering of documents in a folder--see the "Sections"
explanation below.


Descriptions and Additional Metadata
------------------------------------
If you select a folder or document (of any type) in Google Drive, you 
can add descriptive information by editing the "Description" attribute
on the "Details" pane on the right hand side of the Google Drive page.
This plain text description can be used as a teaser for the folder or document.

Also the description can add metadata to the folder or document by using
YAML markup at the end of the description field.  The YAML markup should
be prefixed by a '---' (YAML document) line.

The only allowed keys for metadata in the "Details" YAML section are:

- author
- email
- summary
- template
- title

These attributes must be specified in lower case


Sections and Folder Metadata
----------------------------
To use the "section" template (similar to Schoolwires or Edline's "group page"),
add this to (at the end of) the "Description" attribute of a Google folder. 
You have to use Shift-Enter to put carriage returns in the "Description" field:

    ---
    template: section

This will cause the "section" template to be used by Pelican, which will build
a sub-navivagation menu with links to the contents of the folder. The links
will be listed in lexicographic (alphabetical) order as described above.  

In case you need to override the lexicographic order of a section, or hide
any items that don't have a leading "\_" title, you can add a ".yml" document
to the folder with the special title "\_folder.yml".

    ---
    template: section
    contents:
      - 
        doc: Technology Overview.md
        title: "Technology In The District"
        summary: "These attributes will override the title and description
        in Google Drive"
      - 
        doc: Social Media
      - 
        doc: "Our 1 to 1 Program"
        title: "Our 1:1 Program"
        template: null

In the example above, the top-level "template: section" indicates that all
documents listed inside the folder will use the "section" template (because
we treat the folder as a section).  Then any documents that will be part of
the section template are listed in order. The "doc" attribute must match
the Google Drive title of the document EXACTLY. For this example, the
downloaded titles (and slugs) for the section will be:

1. Technology In The District (technology-in-the-district)
2. Social Media (social-media)
3. Our 1:1 Program (our-1-1-program)

Note that the title and description for a doc can be overridden as shown,
and some documents within the section can be displayed without the section
template ("template: null" for the "Our 1:1 Program" document.

If the "\_folder.yml" file is present, any other documents inside the
Google Drive folder will be downloaded but will not be shown in the "section"
navigation menu.

Metadata for folders are postprocessed when all the documents and subfolders
have been created, to pick up ordering, hidden attributes and recursively 
contained folders (called "subsections");


Top-Level Navigation
--------------------
TBD

If a YAML file named "\_navmenu.yml" is located in the top level folder of a site,
it is used to build the primary navigation menus for the site.
The "navmenu" is the top-level element in the YAML file.  The "navmenu" is a list of submenus. 
Each submenu or item has a title and a type:

- parent - this is a parent menu, and has a submenu list
- link-local - this is a link to a URL on the same site
- link-external - this is a link to a URL on an external site
- pdf - this is a link to a downloadable PDF
- doc - this is a link to a page or article written in markdown. The name of the page content document is the menu item's title, plus the extension ".md"
- section - this is a link to a folder with a "template: section" description or
containing a \_folder\_.yml file


Breadcrumbs
-----------
We won't do this for now.  There's a thought among UX experts that breadcrumbs are 
not comprehensible for most users.


Specifying and Fixing Local Links
---------------------------------
Intra-site links present in source documents have to be transformed into working 
links in the downloaed and exported documents. Pelican has two macros that can
be embedded in Markdown for these "links to internal content":  "{filename}" and
"{attach}".  See http://docs.getpelican.com/en/3.6.3/content.html#linking-to-internal-content

So, there are several ways to specify internal links in source documents, 
depending on the type of document.

1. Links to Google Docs. As part of the preprocessing phase in Pelican, we build a
map (from exported metadata) from the original Google Doc file ID to the exported
HTML url(s).

a. If an exported page has a link to another Google Doc, and that target doc
was exported into a static HTML page for the site, we change the link in the exported HTML 
to point to the static page.  If the target doc appears in more than one location,
we change the link to the preferred location by selecting the "closest" location
to the source document.

b. If the target doc whas not exported, then the link is left alone.

2. Links to Markdown documents. We follow the Pelican convention, using "{filename}"
or "{attach}" in the links.

3. Links to HTML documents. TBD


Folders
-------
The MIME type for a Google Drive folder is "application/vnd.google-apps.folder".
Folders are downloaded as follows:

1. The name ("title") of the folder and any "description" on the folder
are extracted, a slug is built based on the title, and the description is
saved in a "summary" metadata field. Assume that the title
was "General Information", then the slug would be "general-information".

2. A metadata file named "\_folder\_general-information.yml" 
is created with the sample content shown below. Note that the relative URL in the 
metadata does not end in ".html": 

        ---
        author: Kentfield Schools Webmaster
        date: '2015-11-02T22:15:58.595Z'
        dirname: district
        email: webmaster@kentfieldschools.org
        relative_url: general-information
        slug: general-information
        source_id: 0B93xtFAz_q1FNXNNVXZpLVV5cFk
        source_type: application/vnd.google-apps.folder
        summary: null
        title: General Information
        modified: '2015-11-02T23:13:57.367Z'
        version: '11861'

3. After creating the metadata file, the contents of the folder are 
processed (recursively).


(Native) Google Docs
--------------------
The MIME type for a Google Doc is "application/vnd.google-apps.document".

Google Docs are transformed to .html files in the content folder:

1. The name ("title") of the Google Doc and any "description" on the Doc
are extracted, a slug is built based on the title, and the description is
saved in a "summary" metadata field. Assume that the title
was "Technology Overview", then the slug would be "technology-overview".

2. The file is downloaded to "\_raw\_technology-overview.html". ("\_raw\_" + slug + ".html")

3. Then that file is post processed to pull out the "b" (bold) style and a few
other sanitizing things.  The resultant file is named "technology-overview.html" (slug + ".html")

4. A metadata file named "\_meta\_technology-overview.html.yaml" ("\_meta\_" + slug + "html.yml") 
is created with the sample content shown below. Note that the relative URL in the 
metadata does not end in ".html": 

        ---
        author: Kentfield Schools Webmaster
        basename_raw: _raw_technology-overview.html
        basename: technology-overview.html
        date: '2015-11-17T22:42:51.519Z'
        dirname: district/administration/technology
        email: webmaster@kentfieldschools.org
        exported_type: text/html
        relative_url: technology-overview
        slug: technology-overview
        source_id: 1BbJOxqrdMj74nnpj8yyaL9cxeSvswpoG1Ir048SVeks
        source_type: application/vnd.google-apps.document
        summary: null
        title: Technology Overview
        modified: '2015-11-19T20:00:36.341Z'
        version: '11856'


Markdown Files
--------------
The MIME type for these documents is "text/plain" (after downloading the "exported_type" is
set to "text/x-mardown"). The document name (or "title") must have the ".md" file extension 
to distinguish it from a native Google Doc or plain text file.  Install the "Drive Notepad"
Chrome extension to edit Markdown files natively in Google Drive.

Markdown documents are used where special formatting is required (such as including raw HTML).
Markdown are downloaded to ".md" files in the content folder:

1. The name ("title") of the snippet and any "description" on it
are extracted, the title is stripped of any leading underscore or file extension,
a slug is built based on the stripped title, and the description is
saved in a "summary" metadata field. Assume that the doc name
was "District Overview.md", then the title would be "District Overview" and the 
slug would be "district-overview".

2. The file is downloaded to "\_raw\_district-overview.md". ("\_raw\_" + slug + ".md")

3. In the post-download step, Pelican-compatible metadata is prepended to the Markdown
source.  See http://docs.getpelican.com/en/3.6.3/content.html  The resulting file
is named "district-overview.md".

4. Also, a metadata file named "\_meta\_district-overview.md.yaml" ("\_meta\_" + slug + "md.yml") 
is created with the sample content shown below. Note that the relative URL in the 
metadata does not end in ".html": 

        ---
        author: Kentfield Schools Webmaster
        basename_raw: _raw_district-overview.md
        basename: district-overview.md
        date: '2015-11-03T17:09:34.789Z'
        dirname: district/general-information
        email: webmaster@kentfieldschools.org
        exported_type: text/x-markdown
        relative_url: district-overview
        slug: district-overview
        source_id: 0B93xtFAz_q1FZG1IUGVleHVvbXc
        source_type: text/plain
        summary: null
        title: District Overview
        modified: '2015-11-05T00:10:05.776Z'
        version: '11484'


HTML Pages and Snippets
-----------------------
The MIME type for these documents in Google Drive is 'text/html'. These files should contain
either a full HTML page (including a "head" section, which will be modified by the Pelican
processor), or a snippet such as an "iframe" element.  For snippet files, 
the doc name (or "title") should begin with an underscore (so it is not copied to the
website directly). The doc title for full HTML pages or snippets must have the ".html" file 
extension to distinguish it from a native Google Doc or plain text file.

Raw HTML snippets are downloaded to ".html" files in the content folder:

1. The name ("title") of the snippet and any "description" on it
are extracted, the title is stripped of any leading underscore or file extension,
a slug is built based on the stripped title, and the description is
saved in a "summary" metadata field. Assume that the doc name
was "\_District Map.html", then the title would be "District Map" and the slug would be "district-map".

2. The file is downloaded to "\_district-map.html". ("\_" + slug + ".html" for snippets, slug + ".html" 
for full HTML pages). The "relative\_url" will be (slug + ".html" for snippets and just the slug -- 
without ".html" -- for complete pages).

3. No post-download sanitizing is performed, although the Pelican processor will merge 
information in the HTML "head" element with other metadata, CSS and script files.

4. A metadata file named "\_meta\_\_district-map.html.yaml" ("\_meta\_" + slug + "html.yml") 
is created with the sample content shown below. Note that the relative URL in the 
metadata DOES end in ".html": 

        ---
        author: Kentfield Schools Webmaster
        basename: _district-map.html
        date: '2015-11-02T23:57:33.379Z'
        dirname: district/general-information
        email: webmaster@kentfieldschools.org
        exported_type: null
        relative_url: district-map.html
        slug: district-map
        source_id: 0B93xtFAz_q1Fd3VsTHlCYUE2dDg
        source_type: text/html
        summary: null
        title: District Map
        modified: '2015-11-04T23:21:37.469Z'
        version: '11473'


Media Documents
---------------
".jpg", ".png", ".m4v", ".mp3" and other media documents stored in Google Drive
are also downloaded. Example MIME types are "image/png" or "application/pdf".

Example: For a PDF document named "2015-16 District Calendar.pdf" in Google Drive
the metadata file will contain:

        ---
        author: Kentfield Schools Webmaster
        basename: 2015-16-district-calendar.pdf
        date: '2015-11-02T23:57:33.379Z'
        dirname: district/general-information
        email: webmaster@kentfieldschools.org
        exported_type: null
        relative_url: 2015-16-district-calendar.pdf
        slug: 2015-16-district-calendar
        source_id: 0B93xtFAz_q1Fd3VsTHlCYUE2dDg
        source_type: application/pdf
        summary: null
        title: 2015-16 District Calendar
        modified: '2015-11-04T23:21:37.469Z'
        version: '11473'

More description TBD.


Full List of Metadata Attributes
--------------------------------
Attributes generated by downloader (can be overridden in either the Google Drive Description 
field or in a \_folder.yml file):

- author: The human-readable author name (from Google profile)

- basename: The name of the downloaded and post-processed file.

- basename_raw: The name of the file that was originally created during download 
(or null if no post-processing was done).

- date: The modification date from Google Drive API.

- dirname: The directory path within which the basename and basename\_raw files were created.

- email: The email address of the author.

- exported\_type: The MIME type of the downloaded (and possibly post-processed) file: "text/html", 
"text/x-markdown", "text/x-yaml", image/...", etc.

- relative\_url: The URL that will be produced (relative to the dirname) for the document. Markdown
and Google Doc 

- slug: The URL-friendly (lower-case) title that will be used to create a URL.  The slug should
be unique within a folder and never has a file extension.

- source\_id: The Google Drive id for the document or folder.

- source\_type: The MIME type of the source document as reported by Google Drive.

- summary: The "Description" attribute from Google Drive (stripped of leading and trailing whitespace
and any YAML content that begins with '---'). Can be overridden in a \_folder.yml file.

- template: Any Pelican template name.  If null (or omitted), the default "page" template will be used.

- title: The title of the original Google Drive item, stripped of any special prefixes ("\_" or
the "nn]" prefixes described above).  

- modified: Timestamp of last modification.

- version: Google Drive version number.


Additional attributes found only in \_folder.yml:

- contents: The list of documents to be displayed in the section.

- doc: The source title (or id) for the document to be found in the folder.

- expanded: null or the number (0-9) of subsection levels that will be displayed int the subsection menu.

- hidden: True or false.

- numbering: null or the numbering pattern, (like "1.a.1") to display contents and subsections.

- parent: null or the generated full_url of this folder's parent.

- subsections: The list of child folders (as slugs or relative_urls) to be displayed in the section.

- top: null or the generated full_url of the top-most "section" contaning this folder.


Attributes found only in \_navmenu.yml:

- doc: A link to a page or article written in markdown. The name of the page content document is the menu item's title, plus the extension ".md"

- link_external: A link to a URL on an external site

- link_local: A link to a URL on the same site

- parent: A parent menu that has a submenu list

- pdf: A link to a downloadable PDF

- section: A link to a folder with a "template: section" description or
containing a \_folder\_.yml file

- submenu: A list of links within this menu item.


Pelican Phase and Settings
==========================
After downloading, the Pelican static site generator is run.  For basic information see this
document: http://docs.getpelican.com/en/3.6.3/internals.html

Brief pseudocode of how Pelican works (from pelican/__init__.py):

1. Read arguments and settings from command line and the pelicanconf.py settings file.

2. Create an instance of the Pelican class.

2. Build list of Readers from BaseReader (processes files with 'static' file extension), 
    RstReader ('rst' file extension), MarkdownReader ('md', 'markdown', 'mkd', and 
    'mdown' file extensions), HTMLReader ('htm' and 'html' extensions), 
    and any addtional "enabled" readers imported from the settings file, 
    and map each reader to the file extensions it handles.

3. Watch content, theme and static file folders for changes (that might trigger rebuild).

4. Call Pelican.run:

a. Build list of Generators: ArticlesGenerator, PagesGenerator, TemplatePagesGenerator
    (if 'TEMPLATE_PAGES' is specified), SourceFileGenerator (if 'OUTPUT_SOURCES' is 
    specified), and any custom generators specified in the settings file..

b. Clean the output directory.

c. For each generator, if the generator specifies a 'generate_context' function, call it.
    After all contexts have been generated, send the 'all_generators_finalized' signal.

d. Create a writer object.

e. For each generator, if the generator specifies a 'generate_output' function, call it,
    sending the output to the Pelican writer object. After all output has been generated,
    send the 'finalized' signal.

f. Generate statistics on articles and pages processed.


Here's how the PagesGenerator.generate_context function operates:

1. Loop through all files in 'PAGE_PATHS', excluding those in 'PAGE_EXCLUDES'.  

2. For each file, call the Readers object to find an enabled reader that matches the 
    file extension. The Readers object performs the following:

    a. If no reader is found, or the reader throws an exception, 
    or the reader returns false, the file is not processed and is marked 'failed'. 
    
    b. After reading, the file's content and metadata are packaged in an object of a
    subclass of the Content class--in this case a Page object. 
    
    c. The generator then calls the 'is_valid_content' function,
    which is just a wrapper for the Page object's 'check_properties()' method.
    If some required property is missing, 'is_valid_content' return False,
    the file is not processed further and is marked 'failed'.  
    
    d. If the page's status after reading is not either 'published' or 'hidden',  
    the file is not processed further and is marked 'failed'. 

    e. Otherwise, the Page object crated is added to the 'all_pages' (if published) 
    or 'hidden_pages' lists in the Generator.

3. After all files have been read, the generator calls the Pelican utils' 
    process_translations function to translate pages that have a translation 
    metadata element in them.  Add these translated pages to create the final 
    'translations', 'pages', 'hidden_translations' and 'hidden_pages' lists.

4. Add 'pages' and 'hidden_pages' to the generator's context. Also set the context's
    'PAGES' attribute to the 'pages' list.

5. After all files have been processed, send the 'page_generator_finalized' signal, 
    so other observerss can do something with the context if necessary.


The Readers object does the following to read a file sent from the PageGenerator:

1. Send the 'page_generator_preread' signal.

2. Find the reader associated with the file extension.

3. Set up initial metadata.

4. Call the reader's read method to read the file from disk. Metadata is collected from
    the file as specified for the different types of files processed (see the Pelican
    documentation) and added to the initial metadata.

5. Send the 'page_generator_context' signal.

6. Create and return an instance of the Page class (with the default template 'page').
    Page is subclassed from Content.  In the contructor for a Content object,
    still more metadata is added to the Page object, such as 'override_save_as'
    and 'override_url'.  When the instance has been created, send the 'content_object_init'
    signal.


Here's how the PagesGenerator.generate_output function operates:

1. Loop through all the 'translations', 'pages', 'hidden_translations' and 'hidden_pages'
    lists.

2. For each page, call writer.write_file to create the output. The writer has been
    initialized with an output path, and settings. 
    The 'write_file' method is called with the PageGenerator's 'context', 
    the page's 'template', 'save_as', and 'override_save_as'
    attributes, and the global 'RELATIVE_URLS' setting (to determine whether to 
    write relative or absolute URLs in links). The Jinja2 template is loaded
    by the generator from the correspondingly named HTML file within the
    active theme's 'templates' directory.

3. The writer copies the generator's context into a 'local context' object. 
    If 'RELATIVE_URLS' is set, URLs in the 'local contxext' are rewritten from 
    absolute to relative ones. 

4. The writer calls template.render on the 'local context'.

5. After all the files have been written, send the 'page_writer_finalized' signal, 
    so other observerss can do something with the context or writer if necessary.
