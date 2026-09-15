#testing


from Model.Llama import Model
from prompt.prompting_model import get_prompt
from Gmail.reader import grab_messages_list
from Gmail.sender import send_gmail_msg
import json
from Model.memry.Vector_lib import format_personality
contact_list, message_list, *_ = grab_messages_list()


with open('src\\Model\\memry\\gov.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
format_personality(data)



for i in range(1):

# Create a loop that 

    (From,To,Message,Subject,*_) = Model.message_format_model(contact_list[i],message_list[i])

    From =From
    To = To
    context =Message
    Subject = Subject
    
    
    prompt = get_prompt(Message,data, From, To, Subject )
    
    print(prompt)

    print("NUMBER OF TRIALS", i)
    (output, user_subject) = Model.Llama_model(prompt)
    

    

#Next goal, check if emails are valid or not.
#