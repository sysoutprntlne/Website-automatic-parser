#testing


from Model.Llama import Model
from prompt.prompting_model import get_prompt
from Gmail.reader import grab_messages_list


contact_list, message_list, *_ = grab_messages_list()
x =contact_list[0]
y = message_list[0]
print("THISISTHECONTACTREW", x)
print("THISISMESSAGE", y)