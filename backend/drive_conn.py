from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file('credentials.json')

drive_service = build('drive', 'v3', credentials=creds)
