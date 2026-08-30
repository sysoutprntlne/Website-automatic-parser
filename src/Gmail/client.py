import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build




    

class gmail:
    def __init__(self, SCOPES):
        self.scope = SCOPES
    def gmail_cred_auth(self):   
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            
            if os.path.exists("lib/cred/token.json"):
                creds = Credentials.from_authorized_user_file("lib/cred/token.json", self.scope)

            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "lib/cred/credentials.json", self.scope
                    )

                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run

                with open("lib/cred/token.json", "w") as token:
                    token.write(creds.to_json())

            service = build("gmail", "v1", credentials=creds)

            print("gmail_cred function executed")
            return service, creds

        
        
        