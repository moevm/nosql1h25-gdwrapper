from typing import List, Optional
import os
from django.urls import reverse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from gdwrapper.settings import GD_CREDENTIALS_PATH, GD_FIELDS, GD_SCOPES, GD_TOKEN_PATH, GD_AUTH_CALLBACK_URL
from .exceptions import UserNotAuthenticated


class GoogleApiClient:
    """A client class for interacting with Google Drive API v3.
    
    This class provides methods to retrieve and manage user files and folders on Google Drive,
    including metadata. It also supports operations like deleting files (soon).
    """

    def __init__(self):
        """Build Google Drive API service.
        Tries to find token.json file. If doesn't exists raise.
        """
        if os.path.exists(GD_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(GD_TOKEN_PATH, GD_SCOPES)
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError as e:
                    os.remove(GD_TOKEN_PATH)
                    raise UserNotAuthenticated()   
            self.__service = build("drive", "v3", credentials=creds)
        else: raise UserNotAuthenticated()
    
    @staticmethod
    def authorizeUser() -> Optional[str]:
        """Checks if users token.json file exists and is valid.
        If returns auth url user should be authorized before using API.
        Else return None and it means what user is already authorized.
        Returns:
            Optional[str]: Auth URL
        """
        if os.path.exists(GD_TOKEN_PATH):
            return 
        flow = InstalledAppFlow.from_client_secrets_file(
            GD_CREDENTIALS_PATH, GD_SCOPES,
            redirect_uri=GD_AUTH_CALLBACK_URL
        )
        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url

    @staticmethod
    def createUserToken(code: str):
        """Create and save token.json
        Args:
            code (str): code from request params. Code should be sent by Google on GD_AUTH_CALLBACK_URL
        """
        flow = InstalledAppFlow.from_client_secrets_file(
            GD_CREDENTIALS_PATH, GD_SCOPES,
            redirect_uri=GD_AUTH_CALLBACK_URL
        )
        flow.fetch_token(code=code)
        creds = flow.credentials
        with open(GD_TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    @staticmethod
    def logout():
        if os.path.exists(GD_TOKEN_PATH): os.remove(GD_TOKEN_PATH)

    def getAllFiles(self) -> List[dict]:
        """Make request to Google Drive API to get users files.

        Returns:
            List[dict]: List of files data
        """
        results = (
            self.__service.files()
            .list(q="trashed=false", fields='files({})'.format(', '.join(GD_FIELDS)))
            .execute()
        )
        return results.get("files", [])