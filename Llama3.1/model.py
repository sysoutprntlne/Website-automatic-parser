
from unsloth import FastLanguageModel
import torch
import mlx

from BPE_tokenizer import get_tokenizer


model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3.1-8b-unsloth-bnb-4bit",
    max_seq_length = 2048,
    load_in_4bit = True,
    dtype = None,
)

tokenizer = get_tokenizer()

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

#Data preprcessing




## LORA APPLIED (QUANTIZED) 6005 bits /per weight
# NEED TO complete finetuning


#Goal is to apply tokenizer to model, get data to train model and train