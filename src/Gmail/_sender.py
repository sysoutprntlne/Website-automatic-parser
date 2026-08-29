import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
creds = None


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


def custom_message(Subject, to):

    message = []

    message["Subject"] = Subject
    message["To"] = to
    message["From"] = "Frompeter1999grif@gmail.com"


# Give message back to user
def give_message_back(input, subject, to):
    try:
        service = build("Gmail", "v1", credentials=creds)
        message = EmailMessage()
        message.set_content(input)

        # Encoding

        message_encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_msg = {"raw": message_encoded}
        message = (
            service.users().messages().send(userId="me", body=create_msg).execute()
        )

        print(message["id"] + " message sent!")

    except HttpError as e:
        print(f"error occured: {e}")


print("function executed")
