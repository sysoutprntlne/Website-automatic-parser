



import os
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
import uuid
from ollama import chat
from ollama import ChatResponse

#Added email function in order to access functions such as sending messages
import email_snatch.gmail_API as email_functions



#Create chroama client / connection API




def personality_taker(input_msg_array):
    # takes inputs from users, embeds it and feeds it into ai with prompting
    
    #Input by user 
    """zero_input = input("1/3: ")
    one_input = input("2/3: ")
    two_input = input("3/3: ") """

    #TEST input
    zero_input = """Hey Alex, just wanted to check if we're still good for Saturday. Let me know if anything changes."""

    one_input = """Hi Professor Smith, I wanted to follow up about the assignment and ask if you could clarify the requirements when you have a chance. Thank you."""

    two_input = """Hi Daniel, could you send me the latest version of the API documentation when you get a chance? I want to make sure I'm working with the most recent version."""

    
    
    user_document = [zero_input,one_input,two_input]
    
    client = chromadb.Client()
    collection = client.create_collection("VectorDB")

    auto_ids = [str(uuid.uuid4()) for _ in user_document]
    collection.add(ids= auto_ids, documents= user_document)


    content = ""

    for message in input_msg_array:
        
        user_input = message
        context_personal = collection.query(query_texts= user_input, n_results= 1)
        prompt = f"You are an AI assistant that writes emails on behalf of the user. Your goal is to produce emails that naturally sound like the user wrote them. Match the user's tone, vocabulary, sentence length, punctuation, capitalization, formality, and typical level of detail. Prefer simple, natural, conversational wording over sophisticated or overly polished language. Preserve the user's personality and writing habits while adapting appropriately to the situation. Do not invent information, exaggerate politeness or enthusiasm, or use phrases that sound obviously AI-generated. Keep emails concise unless more detail is necessary. Use the provided examples as style references, but do not copy their wording unless appropriate. Infer the underlying writing style from the examples and apply it to new situations. Output only the completed email unless explicitly asked for an explanation. Write the emails from SAMUEL Context:{context_personal}"
        print("Creating response to email")
        response: ChatResponse = chat(model='llama3.1', messages=[
        {
            'role': 'user',
            'content': prompt,
        },
        ])
        
        email_send = email_functions.give_message_back(response['message']['content'])
        print(response['message']['content'])
        
    # or access fields directly from the response object
  


#===============
#=============== TEST CODE
