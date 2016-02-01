#!/usr/bin/python

import codecs
import os.path
from pprint import pprint as pp
import re
import yaml

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from sanitizer import sanitize_html_file, prepend_markdown_metadata

# List of atributes that users can put in Google Drive, Markdown, HTML, etc.
USER_META_KEYS = [ 
    'author', 'email', 'summary', 'template', 'title'
]

class GDriveDownloader():
    def __init__(self, maxdepth=1000000, verbose=False):
        self.depth = 0
        self.root_path = None
        self.gauth = None
        self.gdrive = None
        self.maxdepth = maxdepth
        self.verbose = verbose
        self.file_list = [ ]
        print "maxdepth %d, verbose %r" % (maxdepth, verbose)

    def authorize(self):
        self.gauth = GoogleAuth()
        self.gauth.LocalWebserverAuth()
        self.gdrive = GoogleDrive(self.gauth)
        self.gauth.Authorize()

    def getLocalTitle(self, item):
        local_title = item['title']
        file_type = None
        # Hyphenated, lower-case slug
        local_title = re.sub(r'[^-._a-z0-9]', '-', local_title, flags=re.IGNORECASE).lower()
        if item['mimeType'] == 'application/vnd.google-apps.document':
            if item['kind'] == 'drive#file' and 'exportLinks' in item and 'text/html' in item['exportLinks']:
                file_type = 'text/html'
        elif item['mimeType'] == 'text/plain' and item['title'].endswith('.md'):
            file_type = 'text/x-markdown'

        if self.verbose:
            print 'localTitle for "%s" kind "%s" mime "%s" ' % (item['title'], item['kind'], item['mimeType'])
            print 'returning "%s" file_type "%s"' % (local_title, file_type)
        return (local_title, file_type)

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
                if self.verbose:
                    print 'split description and meta at %d' % yaml_i
                    print 'description: "%s"' % description
                    print 'meta: %r' % raw_meta
            if len(description) == 0:
                description = None

        gdrive_meta = { }
        if raw_meta is None:
            # No yaml part - create one     
            if description is not None:
                gdrive_meta['summary'] = description
                if self.verbose:
                    print 'returning description in meta: %r' % gdrive_meta
        else:
            # Update yaml part
            if description is not None and 'summary' not in raw_meta:
                raw_meta['summary'] = description
            for key in [k for k in USER_META_KEYS if k in raw_meta and raw_meta[k] is not None]:
                gdrive_meta[key] = raw_meta[key]
            if self.verbose:
                print 'returning meta: %r' % gdrive_meta
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
        local_title, exported_type = self.getLocalTitle(folder_item)
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
                print '  ' * self.depth + 'Created folder "%s" in "%s"' % (local_title, cur_path)

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
            'summary': None, # TODO
            'template': None, # TODO
            'title': folder_item['title'],
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
                print '  ' * self.depth + 'Maximum depth %d exceeded' % self.depth
            return

        if not self.gauth:
            self.authorize()

        item = self.gauth.service.files().get(fileId=fID_from).execute()
        if self.verbose:
            print '  ' * self.depth + 'Recursively downloading "%s" (id: %s)' % (item['title'], item['id'])
            print '  ' * self.depth + 'into folder: %s' % path_to

        if self.depth == 0:
            if item['kind'] == 'drive#file' and item['mimeType'] == 'application/vnd.google-apps.folder':
                self.root_path = path_to
                path_to = self.makeFolder(item, '')
            else:
                print  '  ' * self.depth + 'Top level item is not a folder'
                return

        # Go through children with pagination
        while True:
            result = self.gauth.service.files().list(q='"%s" in parents and trashed = false' % fID_from).execute()

            # Alternative way to get children:
            #   (returns `drive#childReference` instead of `drive#file`)
            # result = self.gauth.service.children().list(folderId=fID_from).execute()
            for child in result['items']:
                if child['kind'] != 'drive#file':
                    print 'Unknown object type (not file or folder): "%s"' % child['kind']
                    pp(child)

                source_type = child['mimeType']
                if source_type == 'application/vnd.google-apps.folder':
                    self.depth += 1
                    new_folder = self.makeFolder(child, path_to)
                    self.recursiveDownloadInto(child['id'], new_folder)

                else:
                    local_title, exported_type = self.getLocalTitle(child)

                    append_html = False
                    if exported_type == 'text/html':
                        append_html = True

                    file_name = local_title
                    if append_html:
                        file_name += '.html'

                    meta_name = '_meta_' + file_name + '.yml'
                    if exported_type in ['text/html', 'text/x-markdown']:
                        file_name = '_raw_' + file_name + '.x'

                    new_file = os.path.join(self.root_path, path_to, file_name)
                    exists_check = os.path.exists(new_file)
                    if self.verbose:
                        print '  ' * (self.depth+1) + 'Trying to download "%s"' % child['title']
                    try:
                        download_url = None
                        if exported_type in ['text/html'] and 'exportLinks' in child and exported_type in child['exportLinks']:
                            download_url = child['exportLinks'][exported_type]
                        elif 'downloadUrl' in child:
                            download_url = child['downloadUrl']

                        file_content = self.getDownloadContent(download_url)
                        bytes_to_copy = len(file_content)
                        with open(new_file, 'w+') as f:
                            f.write(file_content)

                        # Original file name, stripped of .md and .html
                        title = re.sub(r'(^_|\.(md|html)$)', '', child['title'], flags=re.IGNORECASE)
                        # Lower-case slug, stripped of .md and .html

                        slug = relative_url = re.sub(r'(\.(md|html)$)', '', local_title, flags=re.IGNORECASE)
                        if re.search(r'\.(md|html)$', local_title):
                            relative_url += '.html'
                        if slug[:1] == '_':
                            slug = slug[1:]

                        # Pull description from Google Drive
                        gdrive_meta = self.parseGDriveMeta(child)
                        file_meta = {
                            'author': child['lastModifyingUserName'],
                            'basename': file_name,
                            'basename_raw': file_name,
                            'date': child['createdDate'],
                            'dirname': path_to,
                            'email': child['lastModifyingUser']['emailAddress'],
                            'exported_type': exported_type,
                            'relative_url': relative_url,
                            'slug': slug,
                            'source_id': child['id'],
                            'source_type': source_type,
                            'summary': None,
                            'template': None,
                            'title': title,
                            'modified': child['modifiedDate'],
                            'version': child['version']
                        }
                        file_meta.update(gdrive_meta)

                        meta_file = os.path.join(self.root_path, path_to, meta_name)
                        self.writeMeta(meta_file, file_meta)

                        if self.verbose:
                            print '  ' * (self.depth+1) + 'Copied %d bytes to file "%s"' % (bytes_to_copy, local_title)
                        self.file_list.append((path_to, file_name, slug, meta_name, source_type, exported_type))

                    except Exception as e:
                        print 'Failed: %s\n' % e
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

    def postProcess(self):
        self.file_list.sort()
        for dirname, basename_raw, slug, meta_name, source_type, exported_type in self.file_list:
            file_in = os.path.join(self.root_path, dirname, basename_raw)
            meta_file = os.path.join(self.root_path, dirname, meta_name)
            if exported_type == 'text/html':
                basename = slug + '.html'
                file_out = os.path.join(self.root_path, dirname, slug + '.html')
                metadata = self.readMeta(meta_file)
                metadata['basename'] = basename
                sanitize_html_file(file_in, file_out, metadata)
                self.writeMeta(meta_file, metadata)
            elif exported_type == 'text/x-markdown':
                basename = slug + '.md'
                file_out = os.path.join(self.root_path, dirname, slug + '.md')
                metadata = self.readMeta(meta_file)
                metadata['basename'] = basename
                prepend_markdown_metadata(file_in, file_out, metadata)
                self.writeMeta(meta_file, metadata)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Recursively downloads the contents of a Google Drive folder to a path on the local machine')
    parser.add_argument('--verbose', action='store_true', help='print progress on stdout')
    parser.add_argument('src_folder_id', metavar='SRC_FOLDER_ID', help='top level Google Drive folder id')
    parser.add_argument('dest_base', metavar='DEST_BASE', help='top level path')

    args = parser.parse_args()
    downloader = GDriveDownloader(verbose=args.verbose)
    downloader.recursiveDownloadInto(args.src_folder_id, args.dest_base)
    downloader.postProcess()


# permission_list = gauth.service.permissions().list(fileId=file1['id']).execute()
# print 'Changing permission for file "%s" (id: %s)' % (file1['title'], file1['id'])

# new_permission = {
#   'role': 'owner',
#   'type': 'user',
#   'value': 'malthe@socialsquare.dk',
# }

# # print gauth.service.permissions().update(fileId=file1['id']).execute()

# # Try to change permission
# # * Ownership can only be transferred to another user in the same domain # as the current owner.  # (https://support.google.com/drive/answer/2494892?hl=en)
# # * You cannot change permission between personal and Google Apps account (https://productforums.google.com/d/msg/docs/5liCUAfvKUs/y9h7GYQT_z0J)
# #
# ### gauth.service.permissions().insert(fileId=file1['id'], body=new_permission).execute()

# copied_file = {
#   'parents': [{ 'id': '0B-WpRvMKai6WfkxCcXh2UUhVUktjT0dnUEZkdEtaY2E1UUo2dUctTnhIMmxUelVQN3FzZ3M' }], # "Copied from BIT BLUEPRINT" folder
#   # 'title': file1.metadata['title'] + ' copy',
# }

# new_file = gauth.service.files().copy(fileId=file1['id'], body=copied_file).execute()
# pp(new_file)

# # permission_list = gauth.service.permissions().list(fileId=file1['id']).execute()
# # pp(permissions['items'])