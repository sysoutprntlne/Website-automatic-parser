#testing


from Model.Llama import Model
from prompt.prompting_model import get_prompt, user_response
from Gmail.reader import grab_messages_list
from Gmail.sender import send_gmail_msg
from Model.memry.Vector_lib import update_memory_persistent,load_memory_persistent
def start():
    
    contact_list, message_list, *_ = grab_messages_list()


    # load persistent memory with looking at message_list
    personality = load_memory_persistent(message_list)
    print(personality)
    for i in range(5):

    # Create a loop that 

        (From,To,Message,Subject,*_) = Model.message_format_model(contact_list[i],message_list[i])
        

        From =From
        To = To
        context =Message
        Subject = Subject
        
        user_output = user_response(context)
        
        prompt = get_prompt(Message,personality, To, From, Subject, user_output )
        
        print(prompt)

        print("NUMBER OF TRIALS", i)
        (output, user_subject) = Model.Llama_model(prompt)
        print("============================================")
        user_confirm = input("Send message? (Y/N/R): ")        
        print("============================================")

        while True:
            
            if (user_confirm.lower() == "n"):
                break
            elif (user_confirm.lower() == "y"):
                update_memory_persistent(output)
                send_gmail_msg(output, user_subject, To, From)
                break

            elif(user_confirm.lower() == "r"):
                (output, user_subject) = Model.Llama_model(prompt)
                print()
                print("============================================")
                user_confirm = input("Send message? (Y/N/R): ")        
                print("============================================")

                
                
                
            else:
                print("============================================")
                print(f"{user_confirm} is not a valid answer, please try again---")
                print()
                print("============================================")
                user_confirm = input("Send message? (Y/N/R): ") 
                print("============================================")


# This guard triggers the function when run from the terminal



#Next goal, check if emails are valid or not.
