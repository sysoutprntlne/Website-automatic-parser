from email.message import EmailMessage
import base64
import sys
import logging
from googleapiclient.errors import HttpError
from retrying import retry


# Main task: Give message back to user

logger = logging.getLogger(__name__)
    
#Retry logic for function (max attempts = 3)
@ retry( stop_max_attempt_number = 3)
def send_gmail_msg(prompt: str, service: str ) -> None:
    
    
    #Assigns the message variables with prompt input
    (subject, output, To, From, *_)  = len_check(prompt)
    #Forms the general message
    for _ in range(3):
        try:
            #Creates message object
            message = EmailMessage()        
            
            message["Subject"] = subject
            message["To"] = To
            message["From"] = From
            
            message.set_content(output)
            
            
            # Function for the encoding of the message
            create_msg = encoding_process(message)
            
            
            #Attempt for message to execute
            API_response = (
            service.users().messages().send(userId="me", body=create_msg).execute()
            )

            
            print(API_response["id"] + " message sent!")
            print("sending function was executed")
            break
        
        
        except HttpError:
            logger.exception("failed function: send_gmail_msg")      

#+=================================================================


# function for the encoding of message 
def encoding_process(message: EmailMessage ) -> dict:

    message_encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_msg = {"raw": message_encoded}
    
    return create_msg


# Error handle for positional packaging
def len_check(prompt: tuple) -> dict:

    length = len(prompt)
    
    if length >= 4 :
        subject,output,To,From = prompt[:4]

    if length < 4:
        print(f"Insufficent values in prompt. Only {length} values. ")
        sys.exit()
        
    return subject,output,To,From

        