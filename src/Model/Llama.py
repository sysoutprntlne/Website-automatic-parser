import chromadb
from ollama import chat
from ollama import ChatResponse
from pydantic import BaseModel
import Gmail.reader as email_func
import prompt.prompting_model as promptM
# Model -> Prompting, persistent memory, build

import Model.memry.Vector_lib as memory

# ===============
# Getting response output of model
def Llama_model(input):

    class email(BaseModel):
        From: str
        To: str
        Subject: str
        input: str 
    
    print("Model start")


    response: ChatResponse = chat(
        model="llama3.1",
        messages=[
            {
                "role": "user",
                "content": input,
                
            },
        ],
        format= email.model_json_schema()
    )
    
    email = email.model_validate_json(response.message.content)
    
    print(email)
    return email
# =============== TEST CODE

