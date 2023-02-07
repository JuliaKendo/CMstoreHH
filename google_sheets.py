from __future__ import print_function

import os.path

from contextlib import suppress
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError

from notify_rollbar import notify_rollbar
from exceptions import handle_errors, NoEmployeeData, ErrorGoogleSpreadsheetAuth

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def run_google_auth():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
    
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds


@handle_errors()
@notify_rollbar()
def get_resume_ids(spreadsheet_id, sheet_range):
    resume_ids = []

    with suppress(RefreshError, FileNotFoundError):
        creds = run_google_auth()
        service = build('sheets', 'v4', credentials=creds)

        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=sheet_range
        ).execute()
        values = result.get('values', [])

        if not values:
            raise NoEmployeeData

        for row in values:
            resume_ids.append({'name': row[0], 'id': row[1]})
    
        return resume_ids

    raise ErrorGoogleSpreadsheetAuth
