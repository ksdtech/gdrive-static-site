#!/usr/bin/python

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pprint import pprint as pp
import os.path
import re
import yaml

def getLocalTitle(item):
    local_title = item['title']
    file_type = None
    # Hyphenated, lower-case slug
    local_title = re.sub(r'[^-._a-z0-9]', '-', local_title, flags=re.IGNORECASE).lower()
    if item['kind'] == 'drive#file' and 'exportLinks' in item:
        if item['mimeType'] == 'application/vnd.google-apps.document':
            if 'text/html' in item['exportLinks']:
                file_type = 'text/html'
                local_title += '.html'

    print 'localTitle for "%s" kind "%s" mime "%s" ' % (item['title'], item['kind'], item['mimeType'])
    print 'returning "%s" file_type "%s"' % (local_title, file_type)
    return (local_title, file_type)


def getDownloadContent(gauth, download_url):
    content = None
    if download_url:
        resp, content = gauth.service._http.request(download_url)
        if resp.status != 200:
            raise RuntimeError('An error occurred: %s' % resp)
    else:
        # The file doesn't have any content stored on Drive.
        content = ''
    return content


def makeFolder(folder_item, path_to, depth):
    local_title, file_type = getLocalTitle(folder_item)
    new_folder = os.path.join(path_to, local_title)
    exists_check = os.path.exists(new_folder)

    if not exists_check:
        print '  ' * depth + 'Trying to create folder "%s"' % local_title
        os.mkdir(new_folder)
        print '  ' * depth + 'Created folder "%s" in "%s"' % (local_title, path_to)

    folder_metadata = {
        'source_id': folder_item['id'],
        'title': folder_item['title'],
        'source_mime_type': folder_item['mimeType'],
        'date': folder_item['createdDate'],
        'updated': folder_item['modifiedDate'],
        'version': folder_item['version'],
        'author': folder_item['lastModifyingUserName'],
        'email': folder_item['lastModifyingUser']['emailAddress']
    }
    meta_file = os.path.join(new_folder, '_folder_.yml')
    yaml_meta = yaml.safe_dump(folder_metadata, default_flow_style=False,  explicit_start=True)
    with open(meta_file, 'w+') as f:
        f.write(yaml_meta)

    return new_folder

def recursiveDownloadInto(gauth, fID_from, path_to, maxdepth=float('infinity'), __currentDepth=0):

    if __currentDepth > maxdepth:
        return

    item = gauth.service.files().get(fileId=fID_from).execute()
    print '  ' * __currentDepth + 'Recursively downloading "%s" (id: %s)' % (item['title'], item['id'])
    print '  ' * __currentDepth + 'into folder: %s' % path_to

    if __currentDepth == 0:
        if item['kind'] == 'drive#file' and item['mimeType'] == 'application/vnd.google-apps.folder':
            path_to = makeFolder(item, path_to, __currentDepth)
        else:
            print  '  ' * __currentDepth + 'Top level item is not a folder'
            return

    # Go through children with pagination
    while True:
        result = gauth.service.files().list(q='"%s" in parents and trashed = false' % fID_from).execute()
        # Alternative way to get children:
        #   (returns `drive#childReference` instead of `drive#file`)
        # result = gauth.service.children().list(folderId=fID_from).execute()
        for child in result['items']:
            if child['kind'] != 'drive#file':
                print 'Unknown object type (not file or folder): "%s"' % child['kind']
                pp(child)

            local_title, file_type = getLocalTitle(child)
            if child['mimeType'] == 'application/vnd.google-apps.folder':
                new_folder = makeFolder(child, path_to, __currentDepth+1)
                recursiveDownloadInto(gauth, child['id'], new_folder, maxdepth=maxdepth, __currentDepth=__currentDepth+1)

            else:
                new_file = os.path.join(path_to, local_title)
                exists_check = os.path.exists(new_file)
                print '  ' * (__currentDepth+1) + 'Trying to download "%s"' % child['title']
                try:
                    download_url = None
                    if file_type is not None and 'exportLinks' in child and file_type in child['exportLinks']:
                        download_url = child['exportLinks'][file_type]
                    elif 'downloadUrl' in child:
                        download_url = child['downloadUrl']

                    file_content = getDownloadContent(gauth, download_url)
                    bytes_to_copy = len(file_content)
                    with open(new_file, 'w+') as f:
                        f.write(file_content)

                    # Original file name, stripped of .md and .html
                    title = re.sub(r'(^_|\.(md|html)$)', '', child['title'], flags=re.IGNORECASE)
                    # Lower-case slug, stripped of .md and .html
                    relative_url = slug = re.sub(r'(^_|\.(md|html)$)', '', local_title, flags=re.IGNORECASE)

                    source_mime_type = child['mimeType']
                    if source_mime_type in ['text/plain', 'text/html']:
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
                        'summary': description,
                        'source_mime_type': source_mime_type,
                        'exported_file_name': local_title,
                        'exported_mime_type': file_type,
                        'date': child['createdDate'],
                        'updated': child['modifiedDate'],
                        'version': child['version'],
                        'author': child['lastModifyingUserName'],
                        'email': child['lastModifyingUser']['emailAddress']
                    }

                    yaml_meta = yaml.safe_dump(file_metadata, default_flow_style=False,  explicit_start=True)
                    meta_file = os.path.join(path_to, '_meta_' + local_title + '.yml')
                    with open(meta_file, 'w+') as f:
                        f.write(yaml_meta)

                    print '  ' * (__currentDepth+1) + 'Copied %d bytes to file "%s"' % (bytes_to_copy, local_title)
                except Exception as e:
                    print 'Failed: %s\n' % e


        # Get page
        page_token = result.get('nextPageToken')
        if not page_token:
            break

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Recursively downloads the contents of a Google Drive folder to a path on the local machine')
    parser.add_argument('to_path', metavar='TO_PATH', help='a path for the accumulator')
    parser.add_argument('from_folder_id', metavar='TO_FOLDER_ID', help='an integer for the accumulator')

    args = parser.parse_args()

    # Authenticate
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()

    drive = GoogleDrive(gauth)
    gauth.Authorize()

    # Copy folder
    recursiveDownloadInto(gauth, args.from_folder_id, args.to_path) #, maxdepth=0)


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