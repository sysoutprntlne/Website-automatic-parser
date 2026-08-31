from Gmail.client import gmail
from googleapiclient.errors import HttpError
from email.message import EmailMessage
import base64
import sys
from Model.Llama import Llama_model
# Give message back to user


def send_gmail_msg():

    auth = gmail("https://www.googleapis.com/auth/gmail.send")
    service,creds = auth.gmail_cred_auth()
    
    try:
        email = {}

        
        
        message = EmailMessage()
        message.set_content(email["input"])
        output_scheme = Llama_model(input)
        
        email = {}
        
        
        message["Subject"] = email["Subject"]
        message["To"] = email["To"]
        message["From"] = email["From"]
        
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
send_gmail_msg()
