# task is to talk to model and determine what it needs to fix to become correct
from ollama import chat
from ollama import ChatResponse
import src.Model.Llama as evaluation

good_output = "API Documentation;samuel@gmail.com;daniel@gmail.com;Hi Daniel, could you send me the latest version of the API documentation when you get a chance? I want to make sure I'm working with the most recent version."
with open("Model\memoryDB\pirate.json", "r", encoding="utf-8") as file:
    vector_library = file.read()


# Initalization

user_document = vector_library


def eval_model(model_output):

    evaluator_prompt = f"""
    You are an evaluator for a personality-based AI.

    Evaluate the generated response using the provided personality context, reference examples, and original task.

    PERSONALITY CONTEXT:
    {user_document}

    REFERENCE EXAMPLES:
    {good_output}

    GENERATED RESPONSE:
    {model_output}

    Evaluate these areas:

    1. FORMAT
    - Is the response structured as:
    ;subject;from;to;message
    - Are there exactly four fields?
    - Are the fields in the correct order?
    - Do not reject the response simply because the actual values differ from the examples.

    2. PERSONALITY
    - Does the response behave and communicate consistently with the personality?
    - Does the tone, attitude, vocabulary, values, and behavior fit the character?
    - Do not require the response to copy the reference examples.
    - Different wording is acceptable if the personality is consistent.

    3. TASK
    - Does the response actually address the original task?
    - Judge it against the ORIGINAL TASK, not against the reference email.

    4. INFORMATION
    - Are important facts invented?
    - Do not consider normal creative personality expression to be hallucination.
    - Only flag information as invented when it contradicts or improperly adds to the provided context.

    5. NATURALNESS
    - Does the response sound natural for the personality?
    - Avoid judging based solely on whether it sounds like the reference examples.

    IMPORTANT:
    The reference examples demonstrate personality and writing style. They are NOT required to be reproduced literally.

    A response can be different from the reference and still be correct.

    If the response is acceptable, output exactly:
    PASS

    If the response needs improvement, output:
    FAIL;reason

    The reason should briefly explain the specific problem and what the original model should change.

    Do not rewrite the response.
    Do not invent a new task.
    Do not require the response to match the reference's subject, recipient, or message unless the original task requires it.

    Output ONLY PASS or FAIL followed by the reason.
    """
    response: ChatResponse = chat(
        model="llama3.1",
        messages=[
            {
                "role": "user",
                "content": evaluator_prompt,
            },
        ],
    )

    # Splitting the response into different categories

    response_output = response.message.content
    print(response_output)
    responding_evaluation = evaluation.personality_taker(
        input_msg_array=response_output
    )
