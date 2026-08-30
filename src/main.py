


from Gmail import sender, reader
from src.Gmail.client import gmail
from eval_model import evaluate_model
from model.memory import VectorLib
from prompt import prompting_model
#Flow from auth -> Gmail message into model -> model output -> gmail -> 


def main():
    
    #First authenicate 
    gmail_auth = gmail()
    creds, service = gmail_auth.gmail_cred_auth()




    return 99


#===============
print("hellow")
main()