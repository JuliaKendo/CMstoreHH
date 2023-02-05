from __future__ import print_function

import os.path

from environs import Env
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

env = Env()
env.read_env()

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


def get_resume_ids():
    resume_ids = []
    spreadsheet_id = env('GOOGLE_SPREADSHEET_ID')
    range_name = env('GOOGLE_RANGE_NAME')

    creds = run_google_auth()

    try:
        service = build('sheets', 'v4', credentials=creds)

        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        for row in values:
            resume_ids.append({'name': row[0], 'id': row[1]})
    
    except HttpError as err:
        print(err)

    return resume_ids


def main():
    get_resume_ids()


if __name__ == '__main__':
    main()
