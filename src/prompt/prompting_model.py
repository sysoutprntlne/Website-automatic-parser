import json
import re
from Model.memry import Vector_lib



def get_prompt(context, personality_text, From, To, Subject, user_response):
    
    print(personality_text)
    #string parse of important textual information in database
    doc_list = personality_text["documents"][0]
    
   
    # the JSON string
    traits = doc_list  
    if isinstance(traits, str):
        traits = json.loads(traits)
    personality_text = Vector_lib.format_personality(traits)
    
    
    print(traits)
    
    
    
    sender_name = To
    

    if sender_name:
        signature_instruction = (
            f'If the voice and formality of PERSONALITY calls for a sign-off, '
            f'sign the email as "{sender_name}". Adapt the sign-off style to PERSONALITY.'
        )
    else:
        signature_instruction = (
            "No sender name is available. If PERSONALITY calls for a sign-off, "
            "use a closing that fits the voice but do not invent a name."
        )

    prompt = f"""You are drafting an email on behalf of the person in FROM, who is replying to the message in CONTEXT.

PERSPECTIVE: You are writing AS the person in FROM. CONTEXT was sent TO them by someone else (a business, a friend, etc.) — CONTEXT is NOT your own words and you are not that sender. Your reply speaks from FROM's point of view, responding back to whoever sent CONTEXT. Never write as if you are the original sender of CONTEXT defending, explaining, or restating their own message — you are the recipient, replying.

CONTEXT is the incoming email being responded to. Use it ONLY as background — what it was about, what's being replied to. Do NOT copy or imitate its tone, vocabulary, sentence structure, energy level, or specific phrasing — do not lift or closely paraphrase sentences from it. Its writing style and its claims are not things you are asserting; they're what you're responding to.

USER_RESPONSE is what the person in FROM actually wants to say — this is the core content, intent, AND DECISION of the reply. The specific outcome or decision in USER_RESPONSE (agreeing, declining, requesting, confirming, etc.) must be preserved exactly as given — PERSONALITY may change how that decision is phrased, but must NEVER change, soften, reverse, or hedge the decision itself. Do NOT copy USER_RESPONSE's literal wording or tone — only its meaning and decision. USER_RESPONSE is not a message to reply to — it is FROM's own words, to be rewritten in PERSONALITY's voice.

PERSONALITY TRAITS describes character traits, not writing style directly. You must translate these traits into a distinctive voice yourself: invent vocabulary, phrasing, sentence rhythm, and tone that a person with these traits would plausibly use in a real email. Do not write a neutral or generic email that merely references these traits — they must be expressed through HOW you write, not just what you say. Commit fully and consistently to this voice in every sentence, regardless of how CONTEXT or USER_RESPONSE are phrased.

PERSONALITY TRAITS below are the top 10 results from a database query, retrieved based on similarity to the CONTEXT message. They are not a complete or fixed personality profile. Synthesize them into one coherent, consistent voice rather than treating each entry as a separate instruction to satisfy individually. If entries seem to overlap or repeat, do not over-emphasize that trait.

PRIORITY: USER_RESPONSE determines WHAT the email says AND what decision it conveys, from FROM's perspective. PERSONALITY TRAITS determine HOW it's said. CONTEXT is background only — never speak as if you sent it. Never let PERSONALITY's traits override USER_RESPONSE's actual decision.

additionally, SUBJECT parameter must be answered depending on the context of the incoming email.

SIGNATURE: {signature_instruction}

PERSONALITY TRAITS:
{personality_text}

CONTEXT (incoming message being replied to — background only, this is NOT your voice or your words):
{context}

USER_RESPONSE (what FROM wants to communicate, including their decision — rephrase in PERSONALITY's voice, don't copy its wording or tone. Use this to create YOUR response. Do not output a message to respond to this):
{user_response}

FACTS
Only use information explicitly given above. Do not invent names, dates, numbers, or commitments not present in the inputs. If a detail is missing, leave it out.

From: {From}
To: {To}
Subject: {Subject}

OUTPUT FORMAT
- Return only the email body text — nothing else.
- Do not include a subject line or the word "subject" anywhere in your output, even as a label or with no content after it.
- No labels, no headers.
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