#!/usr/bin/python

import codecs
import os.path
from pprint import pprint as pp
import re
import yaml

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from sanitizer import sanitize_html_file, prepend_markdown_metadata

class GDriveDownloader():
    def __init__(self, maxdepth=1000000, verbose=False):
        self.depth = 0
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
        local_title, file_type = self.getLocalTitle(folder_item)
        new_folder = os.path.join(path_to, local_title)
        exists_check = os.path.exists(new_folder)

        if not exists_check:
            os.mkdir(new_folder)
            if self.verbose:
                print '  ' * self.depth + 'Created folder "%s" in "%s"' % (local_title, path_to)

        folder_metadata = {
            'source_id': folder_item['id'],
            'title': folder_item['title'],
            'source_type': folder_item['mimeType'],
            'date': folder_item['createdDate'],
            'updated': folder_item['modifiedDate'],
            'version': folder_item['version'],
            'author': folder_item['lastModifyingUserName'],
            'email': folder_item['lastModifyingUser']['emailAddress']
        }
        meta_file = os.path.join(new_folder, '_folder_.yml')
        yaml_meta = yaml.safe_dump(folder_metadata, default_flow_style=False,  explicit_start=True)
        with codecs.open(meta_file, 'w+', 'utf-8') as f:
            f.write(yaml_meta)

        return new_folder

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
                path_to = self.makeFolder(item, path_to)
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

                local_title, exported_type = self.getLocalTitle(child)
                if child['mimeType'] == 'application/vnd.google-apps.folder':
                    self.depth += 1
                    new_folder = self.makeFolder(child, path_to)
                    self.recursiveDownloadInto(child['id'], new_folder)

                else:
                    append_html = False
                    source_type = child['mimeType']
                    if exported_type == 'text/html':
                        append_html = True

                    file_name = local_title
                    if append_html:
                        file_name += '.html'

                    meta_name = '_meta_' + file_name + '.yml'
                    if exported_type in ['text/html', 'text/x-markdown']:
                        file_name = '_raw_' + file_name

                    new_file = os.path.join(path_to, file_name)
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

                        relative_url = slug = re.sub(r'(^_|\.(md|html)$)', '', local_title, flags=re.IGNORECASE)
                        if re.search(r'\.(md|html)$', local_title):
                            relative_url += '.html'

                        # Pull description from Google Drive
                        # TODO: if there is '---' at the end of description
                        #    parse remaining bits as yaml.
                        description = None
                        if 'description' in child:
                            description = child['description'].strip()
                            if len(description) == 0:
                                description = None

                        file_metadata = {
                            'source_id': child['id'],
                            'title': title,
                            'slug': slug,
                            'relative_url': relative_url,
                            'source_type': source_type,
                            'exported_type': exported_type,
                            'dirname': path_to,
                            'basename': file_name,
                            'summary': description,
                            'date': child['createdDate'],
                            'updated': child['modifiedDate'],
                            'version': child['version'],
                            'author': child['lastModifyingUserName'],
                            'email': child['lastModifyingUser']['emailAddress']
                        }

                        yaml_meta = yaml.safe_dump(file_metadata, default_flow_style=False,  explicit_start=True)
                        meta_file = os.path.join(path_to, meta_name)
                        with codecs.open(meta_file, 'w+', 'utf-8') as f:
                            f.write(yaml_meta)

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

    def postProcess(self):
        self.file_list.sort()
        for dirname, basename, slug, meta_name, source_type, exported_type in self.file_list:
            if exported_type == 'text/html':
                file_in = os.path.join(dirname, basename)
                file_out = os.path.join(dirname, slug + '.html')
                metadata = yaml.load(codecs.open(os.path.join(dirname, meta_name), 'r', 'utf-8'))
                sanitize_html_file(file_in, file_out, metadata)
            elif exported_type == 'text/x-markdown':
                file_in = os.path.join(dirname, basename)
                file_out = os.path.join(dirname, slug + '.md')
                metadata = yaml.load(codecs.open(os.path.join(dirname, meta_name), 'r', 'utf-8'))
                prepend_markdown_metadata(file_in, file_out, metadata)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Recursively downloads the contents of a Google Drive folder to a path on the local machine')
    parser.add_argument('--verbose', action='store_true', help='print progress on stdout')
    parser.add_argument('src_folder_id', metavar='SRC_FOLDER_ID', help='top level Google Drive folder id')
    parser.add_argument('dest_path', metavar='DEST_PATH', help='top level path')

    args = parser.parse_args()
    downloader = GDriveDownloader(verbose=args.verbose)
    downloader.recursiveDownloadInto(args.src_folder_id, args.dest_path)
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