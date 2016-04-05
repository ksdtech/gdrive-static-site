import httplib2
import webbrowser

from oauth2client import client
from oauth2client.file import Storage
from apiclient.discovery import build

class DriveServiceAuth(object):

    def __init__(self, secrets_path, credentials_path, 
            scope='https://www.googleapis.com/auth/drive',
            api_version='v2'):
        self.http_auth = None
        self.service = None
        self.scope = scope
        self.api_version = api_version
        self.secrets_path = secrets_path
        self.credentials_path = credentials_path
        self.storage = None

    def get_storage(self):
        if not self.storage:
            self.storage = Storage(self.credentials_path)
        return self.storage

    def create_credentials(self):
        flow = client.flow_from_clientsecrets(self.secrets_path,
            scope=self.scope,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob')

        auth_uri = flow.step1_get_authorize_url()
        webbrowser.open(auth_uri)
        auth_code = raw_input('Enter the auth code: ')
        credentials = flow.step2_exchange(auth_code)
        if credentials:
            self.get_storage().put(credentials)
        return credentials

    def build_service(self):
        credentials = self.get_storage().get()
        if not credentials:
            print('No credentials at %s' % self.credentials_path)
            credentials = self.create_credentials()
            if not credentials:
                print('Could not create credentials')
                sys.exit(1)

        self.http_auth = credentials.authorize(httplib2.Http())
        self.service = build('drive', self.api_version, http=self.http_auth)
        return self.service
