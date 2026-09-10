from ollama import chat
from ollama import ChatResponse
from pydantic import BaseModel
 
# Model -> Prompting, persistent memory, build

# ===============
# Getting response output of model

class Model:
    
    

    def Llama_model(input, BaseModel=BaseModel, chat=chat, ChatResponse = ChatResponse ):

        class email(BaseModel):
            
            subject: str
            output: str 

        print("Model start")


        response: ChatResponse = chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": input,
                    
                },
            ],
            format= email.model_json_schema(),
            options={"temperature": 0}
        )
        # how to change to not rely on other methods
        email = email.model_validate_json(response.message.content)
        
        output = email.output
        user_subject = email.subject


        print("Model has responded")
        return output, user_subject

    def message_format_model(contact_list: list, message_list: list) -> str:

        input = f"Correctly sort messages, subject, to, and from. Raw message: {message_list} Raw Contact: {contact_list}" 

        class format_model(BaseModel):
            From: str
            To: str
            Message: str
            Subject: str
            
        response: ChatResponse = chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": "Correctly find and parse the correct pairing emails and conversations ( From, To, message)",
                    
                },
            ],
            format= format_model.model_json_schema(),
            options={"temperature": 0}
                    
        )
        format_model = format_model.model_validate_json(response.message.content)
        
        From = format_model.From
        To = format_model.To
        Message = format_model.Message
        Subject = format_model.Subject
        
        print("message formatting complete")

        return (From, To, Message, Subject)