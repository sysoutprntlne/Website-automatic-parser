from Gmail.client import gmail
from email.message import EmailMessage
import base64
import sys
from Model.Llama import Llama_model, message_format_model
# Give message back to user


def send_gmail_msg(prompt):

    auth = gmail("https://www.googleapis.com/auth/gmail.send")
    service,creds = auth.gmail_cred_auth()
    
    
    try:
        subject,output= Llama_model(prompt)
        To, From = message_format_model(prompt)
        
        message = EmailMessage()        
        
        message["Subject"] = subject
        message["To"] = To
        message["From"] = From
        message.set_content(output)

        message_encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_msg = {"raw": message_encoded}
        message = (
        service.users().messages().send(userId="me", body=create_msg).execute()
        )


        print(message["id"] + " message sent!")

    except AttributeError as e:
        print(f"error occured: {e}")
        sys.exit


    print("function executed")

#+=================================================================
