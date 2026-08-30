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


# Give message back to user
def send_gmail_msg( input, subject, to):
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





send_gmail_msg("Example", "subject example",  )