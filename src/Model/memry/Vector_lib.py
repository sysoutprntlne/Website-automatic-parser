# get vector library for rag mode
import chromadb
import json
import random
chroma_client = chromadb.PersistentClient(path = "./chromadata")
collection = chroma_client.get_or_create_collection(name = "persisent_db")



def format_personality(personality_json):

        return "\n".join(f"- {item}" for item in personality_json)


#took out other persistnet memory modules in funcitons

def load_memory_persistent(message_list):
    collection = chroma_client.get_or_create_collection(name = "persisent_db")
    personality = []

    for message in message_list:
        user_input = message
        personality = collection.query(query_texts= user_input, n_results= 10) 

        print("Load_Memory_persistent")
        print(personality)
    return personality

def update_memory_persistent(input):
    collection = chroma_client.get_or_create_collection(name = "persisent_db")


    id_gen = random.randint(1,1000) 
    collection.add(documents= [input], ids= [str(id_gen)])
    print(collection.query(query_texts= input, n_results= 10) )
    
    
    
    
    

    

    



