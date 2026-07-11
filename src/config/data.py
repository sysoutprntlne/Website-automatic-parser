from unsloth.chat_templates import get_chat_template
from unsloth.chat_templates import CHAT_TEMPLATES
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.trainers import BpeTrainer
from datasets import load_dataset


#dataset list
print(list(CHAT_TEMPLATES.keys()))

#Tokenizers

tokenizer = Tokenizer(BPE())
tokenizer.pre_tokenizer = Whitespace()

#Speical TOKEN
trainer = BpeTrainer(special_tokens = ["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"])
tokenizer.train(files=["wiki.train.raw"])
tokenizer = get_chat_template(tokenizer, chat_template = "llama-3.1")



#LOOP OF CHAT TEMPLATE (LLAMA 3.1)

tokenizer = get_chat_template(
    tokenizer,
    chat_template = "gemma-3", # change this to the right chat_template name
)

def formatting_prompts_func(examples):
    convos = examples["conversations"]
    texts = [tokenizer.apply_chat_template(convo, tokenize = False, add_generation_prompt = False) for convo in convos]
    
    print("Done")
    
    return { "text" : texts, }


#Load dataset (Email)
ds = load_dataset("GalaktischeGurke/emails_5500_to_7500")

formatting_prompts_func(ds)