#testing


from Model.Llama import Model
from prompt.prompting_model import get_prompt, user_response
from Gmail.reader import grab_messages_list
from Gmail.sender import send_gmail_msg
import json
from Model.memry.Vector_lib import format_personality

def main():
    
    contact_list, message_list, *_ = grab_messages_list()


    with open('src\\Model\\memry\\dog.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    format_personality(data)



    for i in range(1):

    # Create a loop that 

        (From,To,Message,Subject,*_) = Model.message_format_model(contact_list[i],message_list[i])

        From =From
        To = To
        context =Message
        Subject = Subject
        
        user_output = user_response(context)
        
        prompt = get_prompt(Message,data, From, To, Subject, user_output )
        
        print(prompt)

        print("NUMBER OF TRIALS", i)
        (output, user_subject) = Model.Llama_model(prompt)
        print("============================================")
        user_confirm = input("Send message? (Y/N): ")        
        print("============================================")

        while True:
            
            if (user_confirm.lower == "n"):
                break
            elif (user_confirm.lower == "y"):
                send_gmail_msg(output, user_subject, To, From)
            else:
                print("============================================")
                print(f"{user_confirm} is not a valid answer, please try again---")
                print()
                print("============================================")
                user_confirm = input("Send message? (Y/N): ") 
                print("============================================")


# This guard triggers the function when run from the terminal
if __name__ == "__main__":
    main()


#Next goal, check if emails are valid or not.
#Have direct inputs