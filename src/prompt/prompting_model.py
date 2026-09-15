import json

# Utilize this file to house

# Where all prompting functions live;


# Getting the prompt for model
def get_prompt(context, personality_text, From, To, Subject, user_response):


    prompt = f"""You are drafting an email on behalf of a user, replying to the message in CONTEXT.

CONTEXT is the incoming email being responded to. Use it ONLY as background — what it was about, what's being replied to. Do NOT copy or imitate its tone, vocabulary, sentence structure, or energy level. Its writing style is irrelevant.

USER_RESPONSE is what the user actually wants to say — this is the core content and intent of the reply. Treat it as the primary fact and instruction for what the email must communicate. Do NOT copy its tone, wording, or phrasing directly, even if it is blunt, rude, or casual — its literal language is not the target style, only its meaning is.

PERSONALITY describes character traits, not writing style directly. You must translate these traits into a distinctive voice yourself: invent vocabulary, phrasing, sentence rhythm, and tone that a person with these traits would plausibly use in a real email. Do not write a neutral or generic email that merely references these traits — they must be expressed through HOW you write, not just what you say. Commit fully and consistently to this voice in every sentence, regardless of how CONTEXT or USER_RESPONSE are phrased.

PRIORITY: USER_RESPONSE determines WHAT the email says. PERSONALITY determines HOW it's said. CONTEXT is background only. Never let CONTEXT's or USER_RESPONSE's literal tone override PERSONALITY's voice.

PERSONALITY TRAITS:
{personality_text}

CONTEXT (incoming message being replied to — background only, ignore its style):
{context}

USER_RESPONSE (what the user wants to communicate — rephrase in PERSONALITY's voice, don't copy its wording or tone):
{user_response}

FACTS
Only use information explicitly given above. Do not invent names, dates, numbers, or commitments not present in the inputs. If a detail is missing, leave it out.

From: {From}
To: {To}
Subject: {Subject}

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

def user_response(output):
    print(output)
    print()
    print()
    print()

    response = input("Response: ")
    print("sending to model...")
    return response