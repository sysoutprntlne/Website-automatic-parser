import os
import chromadb


#Create chroama client / connection API
client = chromadb.Client()

collection = client.create_collection("VectorDB")

collection.add(ids = ["1", "22", "333"], documents= ["i am a pineapple under a tree", "he is not apple above forest", "how"])


results = collection.query(
   query_texts=  ["i am a pineapple under a tree", "the oracle speaks"],
   ids= ["1","22","333"],
    n_results= 2
)

print(results)

