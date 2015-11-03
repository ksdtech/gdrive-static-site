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
python copy_folder.py /Users/pz/Projects/_active/jekyll-gdocs/project 0B93xtFAz_q1FYS04RFJfQkJkdGM
```
