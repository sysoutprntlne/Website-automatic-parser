# get vector library for rag mode
def get_vector_library():

    with open("Model\memoryDB\pirate.json", "r", encoding="utf-8") as file:
        vector_library = file.read()

    return vector_library
