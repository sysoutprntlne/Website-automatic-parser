#putting everything into larger pieces

from Gmail.client import gmail
from Gmail.reader import grab_messages_list
from Gmail.sender import send_gmail_msg
from prompt.prompting_model import get_prompt, get_personality
from Model.Llama import Llama_model, message_format_model

def __main__():
    
    #First authenicate 
    test_auth = gmail(["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"])
    service = test_auth.gmail_cred_auth()
    message_list, contact_list, *_ = grab_messages_list(service)
    Person_data = "src\Model\memry\pirate.json"
    personality = get_personality(Person_data)
    prompt = get_prompt(personality)
    
    
    
    
    #Build model, taking list as input, let be input, make it modeular

    for i in range(3):
    
        (output, subject) = Llama_model(prompt)
        
        send_gmail_msg(output[i], test_auth[1] )
    
    
    
    # loop to repspond multiple times for each message
    
    
    
    
    for i in range(3):
        
        From, To, Message, Subject = message_format_model(contact_list[i],message_list[i])
        prompt = get_prompt(Message[i],personality, From[i], To[i], Subject[i] )    
        output = Llama_model(prompt)
        
        send_gmail_msg(prompt = output)
    #inject prompt
    
    """  for i in range(1):
        
        personality = get_personality("src\Model\memry\pirate.json")
        prompt = get_prompt(message_list[i],contact_list[i],personality)
        send_gmail_msg(prompt)"""
    


    #Send to model
    





#===============
__main__()