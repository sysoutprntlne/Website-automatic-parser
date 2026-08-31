
from Gmail.client import gmail
from Gmail.reader import grab_messages_list
from Gmail.sender import send_gmail_msg
from eval_model.eval import eval_model
from Model.memry.Vector_lib import get_vector_library
from prompt.prompting_model import get_prompt, prompt_splitting, get_personality
from Model.Llama import Llama_model,message_format_model

def __main__():
    
    #First authenicate 
    test_auth = gmail(["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"])
    service, creds = test_auth.gmail_cred_auth()
    message_list, contact_list = grab_messages_list(service)
    
    personality = get_personality("src\Model\memry\pirate.json")
    
    
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