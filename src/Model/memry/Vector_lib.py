# get vector library for rag mode
import json

def get_vector_library():

    with open("src\Model\memry\pirate.json", "r", encoding="utf-8") as file:
        return str(file)
