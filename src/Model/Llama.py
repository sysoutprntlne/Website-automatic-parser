





import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from ollama import chat
from ollama import ChatResponse
import src.Model.eval_model.eval as evaluation
#Added email function in order to access functions such as sending messages
import src.Model.Gmail._reader as email_func

#Model -> Prompting, persistent memory, build


#===============

input_message = email_func.grab_messages_list()
client = chromadb.PersistentClient("./chromaDB")
collection = client.get_or_create_collection("chromaDB")   
    
#Splitting function
def prompt_splitting(response_output):
    
    splitting = repr(response_output).split
    
    input = splitting[6]
    subject = splitting[3]
    to = splitting[5]
    
    print(
        "input: " + input, "\n",
        "subject:  " + subject,  "\n",
        "to: " +  to
    )
    
def get_prompt(context_personal):
    prompt = f"""
            
        
        Write this email with the goal to match their personality. Match the style in the provided context. Keep it natural, concise, and do not invent information.

        Return ONLY:
        ;subject;from;to;message

            These returned values must be filled with the information it is labeled as. do not include the labels with it.

            Exactly 4 fields separated by 3 semicolons. No labels, explanations, quotes, or extra text.
            
            Evaluate in the end that you correctly answered the prompt.

        CONTEXT:
        {context_personal}
        """
    return prompt

def get_response_output(prompt= get_prompt(email_func.grab_messages_list())):
     
     response: ChatResponse = chat(model='llama3.1', messages=[
        {
            'role': 'user',
            'content': prompt,
        },
        ])
     response_output = response.message.content
    
     print(response_output)
     return response_output
 
def get_vector_library():
    with open("Model\memoryDB\pirate.json", "r", encoding= "utf-8") as file:
        vector_library = file.read()
    
    return vector_library


def personality_taker(input_msg_array) -> int:

    #Initalization 
    user_document = get_vector_library()
    collection.add( ids = ["id1"], documents= user_document)

    content = ""

    for message in input_msg_array:
        
        user_input = message
        context_personal = collection.query(query_texts= user_input, n_results= 1)    
        output = get_response_output()
        try:
           
            prompt_splitting(output) 
           
            print("Evaluation has now begun")
            responding = evaluation.eval_model(get_response_output)
            
           # email_rsp = email_func.give_message_back(input, subject, to = "jun.olea1000@gmail.com")

        except IndexError as e:
            print("error occured: " + e  )
            personality_taker(input_msg_array=input_message)
            
            
    
        # Extract the message using its index position (0-indexed)

    

        
                
    # or access fields directly from the response object
 
#=============== TEST CODE

get_response_output()