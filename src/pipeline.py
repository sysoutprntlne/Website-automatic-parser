#putting everything into larger pieces

from Gmail.client import gmail
from Gmail.reader import grab_messages_list
from Gmail.sender import send_gmail_msg
from prompt.prompting_model import get_prompt, get_personality
from Model.Llama import Model


def __main__():
    
    
    #First authenicate 
    Person_data = "src\Model\memry\pirate.json"
    personality = get_personality(Person_data)

    test_auth = gmail.gmail_cred_auth()
    print("auth passed---")
    
    
    
    message_list, contact_list, *_ = grab_messages_list()
    (From,To,Message,Subject,*_) = Model.message_format_model(message_list,contact_list)
            
    #Build model, taking list as input, let be input, make it modeular

    for i in range(3):
    
        
        
        prompt = get_prompt(Message[i],personality, From[i], To[i], Subject[i] )
        (output, user_subject) = Model.Llama_model(prompt)

        send_gmail_msg(output, user_subject, To = From[i], From = To[i]  )

    
    
    # loop to repspond multiple times for each message
    
    
    
    
 
    #Send to model
    





#===============
__main__()