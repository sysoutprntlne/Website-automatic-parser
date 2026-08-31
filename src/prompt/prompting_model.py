import json

# Utilize this file to house

# Where all prompting functions live;


# Getting the prompt for model


def get_prompt(context, personality):
    prompt = f"""
            
        
        Write this email with the goal to match their personality. Match the style in the provided context. Keep it natural, concise, and do not invent information.


            These returned values must be filled with the information it is labeled as. do not include the labels with it.
            
            Evaluate in the end that you correctly answered the prompt.

        CONTEXT:
        {context}
        
        personality:
        {personality}
        """
    return prompt

# split the output prompt into email format
def prompt_splitting(response_output):

    splitting = repr(response_output).split

    input = splitting[6]
    subject = splitting[3]
    to = splitting[5] 

    print("input: " + input, "\n", "subject:  " + subject, "\n", "to: " + to)

def get_personality(character):
    
    with open(character, "r") as file:
        data = json.load(file)

    json_string = json.dumps(data, indent=4)
    return json_string

personality = get_personality("src\Model\memry\pirate.json")
get_prompt("example text", personality)