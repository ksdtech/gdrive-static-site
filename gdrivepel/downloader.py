from __future__ import print_function

import codecs
import os.path
from pprint import pprint as pp
import re
import yaml

from drive_service import DriveServiceAuth

from sanitizer import (slugify, make_raw_filename, make_meta_filename, 
    sanitize_html_file, prepend_markdown_metadata)

# List of atributes that users can put in Google Drive, Markdown, HTML, etc.
USER_META_KEYS = [ 
    'author', 'email', 'summary', 'template', 'title', 'export_as'
]

# Typical export_as formats
GDRIVE_EXPORT_AS = {
    'html': 'text/html',
    'txt': 'text/plain',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'zip': 'application/zip',
    'odt': 'application/vnd.oasis.opendocument.text',
    'rtf': 'application/rtf',
    'pdf': 'application/pdf'
}

class GDriveDownloader():
    def __init__(self, maxdepth=1000000, verbose=False):
        secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client_secrets.json')
        credentials_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.json')
        print(secrets_path)
        sys.exit(1)
        self.drive_auth = DriveServiceAuth(secrets_path, credentials_path)
        self.drive_service = None
        self.depth = 0
        self.root_path = None
        self.gauth = None
        self.gdrive = None
        self.maxdepth = maxdepth
        self.verbose = verbose
        self.file_list = [ ]
        print('GDriveDownloader maxdepth %d, verbose %r' % (maxdepth, verbose))

    def initService(self):
        self.drive_service = self.drive_auth.build_service()

    def getLocalTitle(self, item, metadata=None):
        local_title = None
        cleaned_title = None
        sort_priority = None
        sorted_title = None
        title = item['title'].strip()

        file_type = None
        if item['mimeType'] == 'application/vnd.google-apps.document':
            if item['kind'] == 'drive#file' and 'exportLinks' in item:
                file_type = 'text/html'

                # Override html export
                if metadata is not None and 'export_as' in metadata:
                    export_as = metadata['export_as']
                    file_type = GDRIVE_EXPORT_AS.get(export_as, None)
                    if file_type is None:
                        print('%s: export_as %s not in %r, using html' % (title, export_as, GDRIVE_EXPORT_AS.keys()))
                        file_type = 'text/html'
                    elif export_as == 'pdf' and title[-4:].lower() != '.pdf':
                        title += '.pdf'

                if file_type not in item['exportLinks']:
                    print('%s: unable to export type %s' % (title, file_type))
                    file_type = None
        elif item['mimeType'] == 'text/plain' and title.endswith('.md'):
            file_type = 'text/x-markdown'

        m = re.match(r'^(([0-9]{3})\]\s*)(.+)$', title)
        if m:
            # Hyphenated, lower-case slug
            title = m.group(3)
            local_title = slugify(title)
            sort_priority = int(m.group(2))
            # Original file name, stripped of leading underscore or trailing extensions
            cleaned_title = re.sub(r'(^_|[_]*\.(pdf|yml|md|html)$)', '', title, flags=re.IGNORECASE)
            sorted_title = m.group(2) + ']' + cleaned_title
        else:
            # Hyphenated, lower-case slug
            local_title = slugify(title)
            sort_priority = 999
            # Original file name, stripped of leading underscore or trailing extensions
            cleaned_title = re.sub(r'(^_|[_]*\.(pdf|yml|md|html)$)', '', title, flags=re.IGNORECASE)
            sorted_title = '999]' + cleaned_title

        if self.verbose:
            print('localTitle for "%s" kind "%s" mime "%s" ' % (item['title'], item['kind'], item['mimeType']))
            print('returning "%s" file_type "%s"' % (local_title, file_type))
        return (local_title, cleaned_title, sorted_title, sort_priority, file_type)

    # Pull description from Google Drive
    # If there is '---' at the end of description, parse remaining bits as yaml.
    def parseGDriveMeta(self, item):
        description = None
        raw_meta = None
        if 'description' in item:
            description = item['description'].strip()
            yaml_i = description.find('---')
            if yaml_i >= 0:
                raw_meta = yaml.load(description[yaml_i:].strip())
                description = description[:yaml_i].strip()
            if len(description) == 0:
                description = None

        gdrive_meta = { }
        if raw_meta is None:
            # No yaml part - create one     
            if description is not None:
                gdrive_meta['summary'] = description
        else:
            # Update yaml part
            if description is not None and 'summary' not in raw_meta:
                raw_meta['summary'] = description
            for key in [k for k in USER_META_KEYS if k in raw_meta and raw_meta[k] is not None]:
                gdrive_meta[key] = raw_meta[key]
        return gdrive_meta

    def getDownloadContent(self, download_url):
        content = None
        if download_url:
            resp, content = self.gauth.service._http.request(download_url)
            if resp.status != 200:
                raise RuntimeError('An error occurred: %s' % resp)
        else:
            # The file doesn't have any content stored on Drive.
            content = ''
        return content

    def makeFolder(self, folder_item, path_to):
        local_title, cleaned_title, sorted_title, sort_priority, exported_type = self.getLocalTitle(folder_item)
        cur_path = None
        new_path = None
        new_folder = None
        if path_to == '':
            cur_path = '/'
            new_path = local_title
            new_folder = os.path.join(self.root_path, local_title)
        else:
            cur_path = os.path.join('/', path_to)
            new_path = os.path.join(path_to, local_title)
            new_folder = os.path.join(self.root_path, new_path)
        exists_check = os.path.exists(new_folder)

        if not exists_check:
            os.mkdir(new_folder)
            if self.verbose:
                print('Created folder "%s" in "%s"' % (local_title, cur_path))

        # Pull description from Google Drive
        gdrive_meta = self.parseGDriveMeta(folder_item)
        folder_meta = {
            'author': folder_item['lastModifyingUserName'],
            'basename': local_title,
            'basename_raw': local_title,
            'date': folder_item['createdDate'],
            'dirname': cur_path,
            'email': folder_item['lastModifyingUser']['emailAddress'],
            'exported_type': exported_type,
            'relative_url': local_title,
            'slug': local_title,
            'source_id': folder_item['id'],
            'source_type': folder_item['mimeType'],
            'sort_priority': sort_priority,
            'sorted_title': sorted_title,
            'summary': None, # TODO
            'template': None, # TODO
            'title': cleaned_title,
            'modified': folder_item['modifiedDate'],
            'version': folder_item['version']
        }
        folder_meta.update(gdrive_meta)

        meta_file = os.path.join(new_folder, '_folder_.yml')
        self.writeMeta(meta_file, folder_meta)
        return new_path

    def recursiveDownloadInto(self, fID_from, path_to):
        if self.depth > self.maxdepth:
            if self.verbose:
                print('Maximum depth %d exceeded' % self.depth)
            return

        if not self.drive_service:
            self.initService()

        item = self.drive_service.files().get(fileId=fID_from).execute()
        if self.verbose:
            print('Recursively downloading "%s" (id: %s)' % (item['title'], item['id']))
            print('  into folder %s at depth %d' % (path_to, self.depth))

        if self.depth == 0:
            if item['kind'] == 'drive#file' and item['mimeType'] == 'application/vnd.google-apps.folder':
                self.root_path = path_to
                path_to = self.makeFolder(item, '')
            else:
                print('Top level item is not a folder')
                return

        # Go through children with pagination
        while True:
            result = self.gauth.service.files().list(q='"%s" in parents and trashed = false' % fID_from).execute()

            # Alternative way to get children:
            #   (returns `drive#childReference` instead of `drive#file`)
            # result = self.gauth.service.children().list(folderId=fID_from).execute()
            for child in result['items']:
                if child['kind'] != 'drive#file':
                    print('Unknown object type (not file or folder): "%s"' % child['kind'])
                    pp(child)

                source_type = child['mimeType']
                if source_type == 'application/vnd.google-apps.folder':
                    self.depth += 1
                    new_folder = self.makeFolder(child, path_to)
                    self.recursiveDownloadInto(child['id'], new_folder)
                    self.depth -= 1
                    # print('Returned from "%s" (id: %s)' % (child['title'], child['id']))
                    # print('  back in folder %s at depth %d' % (path_to, self.depth))

                else:
                    gdrive_meta = self.parseGDriveMeta(child)
                    local_title, cleaned_title, sorted_title, sort_priority, exported_type = self.getLocalTitle(child, gdrive_meta)

                    meta_name = file_name = local_title

                    # Handle .yml files
                    if re.search(r'\.yml$', file_name):
                        # Depending on how you edit or upload .yml files in Google Drive
                        # The mime type reported could be text/plain or application/octet-stream
                        # Avoid improperly dealing with Google Docs or Sheets inadvertently saved with .yml extension
                        if re.match(r'(text|application)\/', source_type) and not re.match(r'application\/vnd\.google-apps', source_type):
                            source_type = 'text/yaml'
                            exported_type = None
                        else:
                            if self.verbose:
                                print('Unknown source type for .yml file: ' % source_type)
                                sys.exit(1)

                    # Handle .html and .md exported files
                    if exported_type == 'text/html':
                        file_name += '.html'

                    raw_file_name = file_name
                    if exported_type in ['text/html', 'text/x-markdown']:
                        raw_file_name = make_raw_filename(file_name)

                    new_file = os.path.join(self.root_path, path_to, raw_file_name)
                    exists_check = os.path.exists(new_file)
                    if self.verbose:
                        print('Trying to download "%s"' % child['title'])
                    try:
                        # Download the file
                        download_url = None
                        if 'exportLinks' in child and exported_type in child['exportLinks']:
                            download_url = child['exportLinks'][exported_type]
                        elif 'downloadUrl' in child:
                            download_url = child['downloadUrl']
                        file_content = self.getDownloadContent(download_url)

                        # Lower-case url, with .md converted to .html
                        relative_url = re.sub(r'\.md$', '.html', local_title, flags=re.IGNORECASE)

                        # Lower-case slug, stripped of .yml, .md, .html, and leading _
                        # .pdf and image extensions are left alone
                        slug = re.sub(r'\.(yml|md|html)$', '', local_title, flags=re.IGNORECASE)
                        if slug[:1] == '_' and relative_url[-5:] == '.html':
                            slug = slug[1:]

                        # Pull description from Google Drive
                        file_meta = {
                            'author': child['lastModifyingUserName'],
                            'basename': file_name,
                            'basename_raw': raw_file_name,
                            'date': child['createdDate'],
                            'dirname': path_to,
                            'email': child['lastModifyingUser']['emailAddress'],
                            'exported_type': exported_type,
                            'relative_url': relative_url,
                            'slug': slug,
                            'source_id': child['id'],
                            'source_type': source_type,
                            'sort_priority': sort_priority,
                            'sorted_title': sorted_title,
                            'summary': None,
                            'template': None,
                            'title': cleaned_title,
                            'modified': child['modifiedDate'],
                            'version': child['version']
                        }
                        file_meta.update(gdrive_meta)

                        if source_type == 'text/yaml':
                            try:
                                source_meta = yaml.load(file_content)
                                if isinstance(source_meta, dict):
                                    file_meta.update(source_meta)
                                else:
                                    raise Exception('YAML object %r is not a dict' % source_meta)
                            except Exception as e:
                                print('Error parsing YAML from %s: %s' % (download_url, e))
                        else:
                            self.writeContent(new_file, file_content)
                            meta_name = make_meta_filename(file_name)

                        meta_file = os.path.join(self.root_path, path_to, meta_name)
                        self.writeMeta(meta_file, file_meta)

                        if self.verbose:
                            print('Write to file "%s" exported as %s' % (new_file, exported_type))
                        if exported_type is not None:
                            self.file_list.append((path_to, raw_file_name, file_name, meta_name, exported_type))

                    except Exception as e:
                        print('  Failed: %s\n' % e)
                        raise

            # Get page
            page_token = result.get('nextPageToken')
            if not page_token:
                break

    def readMeta(self, meta_file):
        metadata = { }
        with codecs.open(meta_file, 'r', 'utf-8') as f:
            metadata = yaml.load(f)
        return metadata

    def writeMeta(self, meta_file, metadata):
        yaml_meta = yaml.safe_dump(metadata, default_flow_style=False,  explicit_start=True)
        with codecs.open(meta_file, 'w+', 'utf-8') as f:
            f.write(yaml_meta)

    def writeContent(self, content_file, content):
        # Using codecs will throw some decoding errors...
        # with codecs.open(content_file, 'w+', 'utf-8') as f:
        with open(content_file, 'w+') as f:
            f.write(content)

    def postProcess(self):
        if self.verbose:
            print('Post-processing %d files' % len(self.file_list))

        for dirname, basename_raw, basename, meta_name, exported_type in self.file_list:
            file_in = os.path.join(self.root_path, dirname, basename_raw)
            file_out = os.path.join(self.root_path, dirname, basename)
            meta_file = os.path.join(self.root_path, dirname, meta_name)
            if exported_type == 'text/html':
                metadata = self.readMeta(meta_file)
                sanitize_html_file(file_in, file_out, metadata)
            elif exported_type == 'text/x-markdown':
                metadata = self.readMeta(meta_file)
                prepend_markdown_metadata(file_in, file_out, metadata)
