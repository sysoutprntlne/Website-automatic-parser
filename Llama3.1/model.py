
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
from datasets import load_dataset
from unsloth.trainer import UnslothTrainer
from transformers import TrainingArguments
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3.1-8b-unsloth-bnb-4bit",
    max_seq_length = 2048,
    load_in_4bit = True,
    dtype = None,
)


model = FastLanguageModel.get_peft_model(
    model,
    r= 16,
    target_mod = ["q_proj", "k_proj", "v_proj", "o_proj"
                ,"gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
    ue_rslora = False,
    loftq_config = None,
)

#Data import

ds = load_dataset("lmsys/lmsys-chat-1m")
ds = ds.map((lambda x: {"text": x["conversations"][0]["value"]}))

# Model training

model_trainer = UnslothTrainer(
    
    model =model,
    tokenizer =tokenizer,
    train_dataset =ds,
    dataset_text_field ="text",
    max_seq_length =2048,
    args=TrainingArguments(
        output_dir="outputs",
        per_device_train_batch_size=2,
        num_train_epochs=1,
    ),
        
)


model_trainer.train()

#Data preprcessing

#build of tokenizer
"""tokenizers = tokenizers.Tokenizer

tokenizer =  get_chat_template(
    tokenizer,
    chat_template = "llama-3.1", # change this to the right chat_template name
)


def data_preprocessing_Func(data):
    convo_Data = data["Conversation"]
    text = tokenizer.ap
    
"""


## LORA APPLIED (QUANTIZED) 6005 bits /per weight
# NEED TO complete finetuning


#Goal is to apply tokenizer to model, get data to train model and train