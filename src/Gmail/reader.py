import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

"""Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """

creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.

if os.path.exists("email_snatch/token.json"):
    creds = Credentials.from_authorized_user_file("email_snatch/token.json", SCOPES)

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "email_snatch/credentials.json", SCOPES
        )

        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run

    with open("email_snatch/token.json", "w") as token:
        token.write(creds.to_json())

service = build("gmail", "v1", credentials=creds)


def grab_messages_list():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail messages.
    """
    message_list = []

    try:
        # Call the Gmail API
        results = (
            service.users().messages().list(userId="me", labelIds=["INBOX"]).execute()
        )
        messages = results.get("messages", [])
        if not messages:
            print("No messages found.")
            return

        for message in messages:
            msg = (
                service.users().messages().get(userId="me", id=message["id"]).execute()
            )

            message_list.append(msg["snippet"])
    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")

    print(message_list)
    return message_list


# Where main action code starts
# =============================
