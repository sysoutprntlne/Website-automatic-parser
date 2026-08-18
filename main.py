import email_snatch.gmail_API as gmail_
import Model.Llama as AI_MODEL
# Gmail --> Get emails, send to model, model take code and responds, 
# Send emails seperately



message_list_ = gmail_.grab_messages_list()

test = AI_MODEL.personality_taker(input_msg_array=message_list_)






