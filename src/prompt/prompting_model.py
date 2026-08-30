# Utilize this file to house

# Where all prompting functions live;


# Getting the prompt for model


def get_prompt():
    prompt = f"""
            
        
        Write this email with the goal to match their personality. Match the style in the provided context. Keep it natural, concise, and do not invent information.

        Return ONLY:
        ;subject;from;to;message

            These returned values must be filled with the information it is labeled as. do not include the labels with it.

            Exactly 4 fields separated by 3 semicolons. No labels, explanations, quotes, or extra text.
            
            Evaluate in the end that you correctly answered the prompt.

        CONTEXT:
        
        """
    return prompt


# split the output prompt into email format
def prompt_splitting(response_output):

    splitting = repr(response_output).split

    input = splitting[6]
    subject = splitting[3]
    to = splitting[5]

    print("input: " + input, "\n", "subject:  " + subject, "\n", "to: " + to)

