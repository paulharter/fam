from google.oauth2 import credentials

from firebase_admin.credentials import Base


from google.auth.transport import requests

_request = requests.Request()

_scopes = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/datastore',
    'https://www.googleapis.com/auth/devstorage.read_write',
    'https://www.googleapis.com/auth/firebase',
    'https://www.googleapis.com/auth/identitytoolkit',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/firebase.database',
]


class CustomToken(Base):
    """A credential initialized from an existing refresh token."""

    _CREDENTIAL_TYPE = 'authorized_user'

    def __init__(self, token, project_id):
        """Initializes a credential from a refresh token JSON file.

        The JSON must consist of client_id, client_secert and refresh_token fields. Refresh
        token files are typically created and managed by the gcloud SDK. To instantiate
        a credential from a refresh token file, either specify the file path or a dict
        representing the parsed contents of the file.

        Args:
          refresh_token: Path to a refresh token file or a dict representing the contents of a
              refresh token file.

        Raises:
          IOError: If the specified file doesn't exist or cannot be read.
          ValueError: If the refresh token configuration is invalid.
        """
        super(CustomToken, self).__init__()

        self._project_id = project_id

        self._g_credential = credentials.Credentials(token=token, scopes=_scopes)

    @property
    def client_id(self):
        return self._g_credential.client_id

    @property
    def client_secret(self):
        return self._g_credential.client_secret

    @property
    def refresh_token(self):
        return self._g_credential.refresh_token

    @property
    def project_id(self):
        return self._project_id


    def get_credential(self):
        """Returns the underlying Google credential.

        Returns:
          google.auth.credentials.Credentials: A Google Auth credential instance."""
        return self._g_credential
