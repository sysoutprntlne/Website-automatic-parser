
from Gmail.client import gmail
from eval_model.eval import eval_model
from Model.memry.Vector_lib import get_vector_library
from prompt.prompting_model import get_prompt, prompt_splitting

def main():
    
    #First authenicate 
    test_auth = gmail(["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"])
    test_auth.gmail_cred_auth()



    return 99


#===============
main()