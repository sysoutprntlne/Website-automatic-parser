
from Gmail.client import gmail
from Gmail.reader import grab_messages_list
from Gmail.sender import send_gmail_msg
from eval_model.eval import eval_model
from Model.memry.Vector_lib import get_vector_library
from prompt.prompting_model import get_prompt, prompt_splitting, get_personality
from Model.Llama import Llama_model
def __main__():
    
    #First authenicate 
    test_auth = gmail(["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"])
    service, creds = test_auth.gmail_cred_auth()
    message = grab_messages_list(service)
    
    
    
    
    #inject prompt
    
    
    for i in range(1):
        
        personality = get_personality("src\Model\memry\pirate.json")
        prompt = get_prompt(i,personality)
        output = Llama_model(prompt)
        send_gmail_msg()

        


    #Send to model
    





#===============
__main__()