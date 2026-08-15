



import os
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
import uuid
from ollama import chat
from ollama import ChatResponse

#Create chroama client / connection API




def personality_taker():
    # takes inputs from users, embeds it and feeds it into ai with prompting
    
    
    zero_input = input("1/3: ")
    one_input = input("2/3: ")
    two_input = input("3/3: ") 

    user_document = [zero_input,one_input,two_input]
    
    client = chromadb.Client()
    collection = client.create_collection("VectorDB")

    auto_ids = [str(uuid.uuid4()) for _ in user_document]
    collection.add(ids= auto_ids, documents= user_document)


    user_input = input("your question")
    context_personal = collection.query(query_texts= user_input, n_results= 1)

    content = ""
    prompt = f"You are an AI assistant that writes emails on behalf of the user named SAMUEL. Your goal is to produce emails that naturally sound like the user wrote them. Match the user's tone, vocabulary, sentence length, punctuation, capitalization, formality, and typical level of detail. Prefer simple, natural, conversational wording over sophisticated or overly polished language. Preserve the user's personality and writing habits while adapting appropriately to the situation. Do not invent information, exaggerate politeness or enthusiasm, or use phrases that sound obviously AI-generated. Keep emails concise unless more detail is necessary. Use the provided examples as style references, but do not copy their wording unless appropriate. Infer the underlying writing style from the examples and apply it to new situations. Output only the completed email unless explicitly asked for an explanation. Write the emails from SAMUEL Context:{context_personal}"

    response: ChatResponse = chat(model='llama3.1', messages=[
    {
        'role': 'user',
        'content': prompt,
    },
    ])
    print(response['message']['content'])
    # or access fields directly from the response object
  


#===============
#=============== TEST CODE

personality_taker()