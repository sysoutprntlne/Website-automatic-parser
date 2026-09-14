import json

# Utilize this file to house

# Where all prompting functions live;


# Getting the prompt for model
def get_prompt(context, personality, From, To, Subject):


    prompt = f"""You are drafting an email on behalf of a user, replying to the message in CONTEXT.

CONTEXT is the incoming email you are responding to. Use it ONLY as a source of facts and content. Do NOT copy or imitate its tone, vocabulary, sentence structure, or energy level, even if it is casual or high-energy. Its writing style is irrelevant to your reply.

PERSONALITY below describes character traits, not writing style directly. You must translate these traits into a distinctive voice yourself: invent vocabulary, phrasing, sentence rhythm, and tone that a person with these traits would plausibly use in a real email. Do not write a neutral or generic email that merely references these traits — the traits must be expressed through HOW you write, not just what you say. Commit fully and consistently to this voice in every sentence, regardless of how casual or energetic CONTEXT is.

PERSONALITY TRAITS:
{personality}

FACTS
Only use information explicitly given below. Do not invent names, dates, numbers, or commitments not present in the inputs. If a detail is missing, leave it out.

From: {From}
To: {To}
Subject: {Subject}

CONTEXT (incoming message to respond to — facts only, ignore its style):
{context}

OUTPUT FORMAT
- Return only the email body text — nothing else.
- No subject line, no labels, no headers.
- No explanation, no commentary, no restating these instructions.
"""
    print("prompt obtained")
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

