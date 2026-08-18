



import os
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
import uuid
from ollama import chat
from ollama import ChatResponse
import Model.eval_model.eval as evaluation
#Added email function in order to access functions such as sending messages
import email_snatch.gmail_API as email_func
    
#===============
client = chromadb.PersistentClient("./chromaDB")
collection = client.get_or_create_collection("chromaDB")
input_message = email_func.grab_messages_list()
def personality_taker(input_msg_array):
    # takes inputs from users, embeds it and feeds it into ai with prompting
    
    #Input by user 
    """zero_input = input("1/3: ")
    one_input = input("2/3: ")
    two_input = input("3/3: ") """

    #vector library 
    
    with open("Model\memoryDB\pirate.json", "r", encoding= "utf-8") as file:
        vector_library = file.read()
    
    #Initalization 
    
    user_document = vector_library


    collection.add( ids = ["id1"], documents= user_document)

    content = ""

    for message in input_msg_array:
        
        user_input = message
        context_personal = collection.query(query_texts= user_input, n_results= 1)    
        
    # Prompt engineered @ CHATGPT to maximize context
            
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
            #Ollama 3.1 8b prompting function
      
        
        print("Creating response to email")
        response: ChatResponse = chat(model='llama3.1', messages=[
        {
            'role': 'user',
            'content': prompt,
        },
        ])
        
        #Splitting the response into different categories 
        
        response_output = response.message.content
        splitting = repr(response_output).split(";")
        
        # A loop to check for split error, but if good, it will move into evaluation
        
        try:
            
            input = splitting[6]
            subject = splitting[3]
            to = splitting[5]
            print(user_input)
            print("response: " + response_output)
        
            print("Evaluation has now begun")
            responding = evaluation.eval_model(response_output)
            
           # email_rsp = email_func.give_message_back(input, subject, to = "jun.olea1000@gmail.com")

        except IndexError:
            print("error occured")
            personality_taker(input_msg_array=input_message)
            
            
        
        # Extract the message using its index position (0-indexed)

    

        
                
    # or access fields directly from the response object
 
#=============== TEST CODE
