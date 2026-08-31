from Gmail.client import gmail
from googleapiclient.errors import HttpError
from email.message import EmailMessage
import base64
import sys

# Give message back to user


def send_gmail_msg( input, subject, to, From):

    auth = gmail("https://www.googleapis.com/auth/gmail.send")
    service,creds = auth.gmail_cred_auth()
    
    try:
        message = EmailMessage()
        
        message.set_content(input)
        
        message["Subject"] = subject
        message["To"] = to
        message["From"] = From
        
        message_encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_msg = {"raw": message_encoded}
        message = (
        service.users().messages().send(userId="me", body=create_msg).execute()
        )


        print(message["id"] + " message sent!")

    except HttpError as e:
        print(f"error occured: {e}")
        sys.exit()


    print("function executed")

#+=================================================================

