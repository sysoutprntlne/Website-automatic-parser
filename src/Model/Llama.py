import chromadb
from ollama import chat
from ollama import ChatResponse

import Gmail.reader as email_func
import prompt.prompting_model as promptM
# Model -> Prompting, persistent memory, build

import Model.memry.Vector_lib as memory

# ===============





# Getting response output of model
def Llama_model(input):
    
    
    
    print("Model start")


    response: ChatResponse = chat(
        model="llama3.1",
        messages=[
            {
                "role": "user",
                "content": input,
            },
        ],
    )
    response_output = str(response.message.content)

    print(response_output)
    return response_output


# =============== TEST CODE

"""get_response_output()  promptM.prompt_splitting(output) 
            print("Evaluation has now begun")
            responding = evaluation.eval_model(get_response_output)
            
        except IndexError as e:
            print("error occured: " + e  )   user_document = memory.get_vectory_library()
    collection.add( ids = ["id1"], documents= user_document)
    input_msg_array = promptM.get_prompt()
    
    for message in input_msg_array:"""
