from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

CREDENTIALS_FILE = "client_secret_1048793730010-dpjsf1ck1g9rdg9acukv41famj92bp0d.apps.googleusercontent.com.json"
TOKEN_FILE = "token.json"


def get_gmail_credentials():

    credentials = None

    if os.path.exists(TOKEN_FILE):

        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    if not credentials or not credentials.valid:

        if credentials and credentials.expired and credentials.refresh_token:

            credentials.refresh(Request())

        else:

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )

            credentials = flow.run_local_server(
                port=0
            )

        with open(TOKEN_FILE, "w") as token:

            token.write(credentials.to_json())

    return credentials