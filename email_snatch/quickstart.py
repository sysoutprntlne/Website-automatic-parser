import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from colorama import Fore, Back, Style, init
import requests

import base64

# If modifying these scopes, delete the file token.json.

  
  
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]

"""Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)


def grab_messages_list():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail messages.
    """
    
    try:
        # Call the Gmail API
        results = (
            service.users().messages().list(userId="me", labelIds=["INBOX"]).execute()
        )
        messages = results.get("messages", [])

        if not messages:
            print("No messages found.")
            return

        print("Messages:")
        for message in messages:
            print(f'Message ID: {message["id"]}')
            msg = (
                service.users().messages().get(userId="me", id=message["id"]).execute()
            )
            print(Fore.BLACK + "Subject: " + Fore.GREEN + f'{msg["snippet"]}')
    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")

import base64
from email.message import EmailMessage

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError





def give_message_back(input):
  #Send to a specific person automatically,
   try:
     
     service = build("Gmail", "v1", credentials= creds)
     
     message = EmailMessage()
     
     message.set_content(input)
     
     message["Subject"] = "Example"
     message["To"] = "jun.olea1000@gmail.com"
     message["From"] = "peter1999grif@gmail.com"

     
     #Encoding
     
     message_encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
     
     create_msg = {"raw": message_encoded}
     message = (
     service.users().messages().send(userId = "me", body = create_msg ).execute()
     )

     print(message["id"] + " message sent!")
     
     
   except HttpError as boom:
     print("error occured: " + HttpError)
  
   print("function executed")     
  
# Where main action code starts
#=============================

give_message_back("this is an !")
