import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,pipeline
)

model_pipeline = pipeline("text-generation", model="meta-llama/Llama-3.1-8B")

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B")
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B", device_map="auto")
# 1. Load Tokenizer & Model on CPU
# Note: We use the standard base model since 4bit is GPU-only.
# For CPU training, 'float16' helps save RAM, but if it causes errors on CPU, change to torch.float32
model_id = "meta-llama/Llama-3.1-8B" 

print("Loading tokenizer and model")
# Essential for Llama-3 padding
if tokenizer.padtoken is None:
    tokenizer.pad_token = tokenizer.eos_token


# 2. Apply LoRA Config (Equivalent to Unsloth's PEFT settings)
peft_config = LoraConfig(
    r=16,
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.0, 
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, peft_config)
model.print_trainable_parameters()

# 3. Data Processing & Chat Template Application
print("Loading and preprocessing dataset...")
# Load a small slice (e.g., 1000 rows) because full training on CPU is incredibly slow
ds = load_dataset("lmsys/lmsys-chat-1m", split="train[:1000]")

def apply_chat_template(sample):
    # Extracts the raw conversation turn list from the dataset
    conversations = sample["conversations"]
    
    # Map the dataset format into the official Hugging Face standard roles: 'user' or 'assistant'
    formatted_messages = []
    for turn in conversations:
        role = "user" if turn["role"] == "user" else "assistant"
        formatted_messages.append({"role": role, "content": turn["value"]})
        
    # Apply official Llama 3.1 Chat Template format automatically
    templated_text = tokenizer.apply_chat_template(
        formatted_messages, 
        tokenize=False, 
        add_generation_prompt=False
    )
    return {"text": templated_text}

# Transform data and tokenize it
ds = ds.map(apply_chat_template)

def tokenize_function(examples):
    return tokenizer(
        examples["text"], 
        truncation=True, 
        max_length=512, # Lowered from 2048 to prevent CPU RAM crashes
        padding=False
    )

tokenized_ds = ds.map(tokenize_function, batched=True, remove_columns=ds.column_names)

# Data collator manages padding dynamic batches efficiently
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

# 4. Model Training Arguments
training_args = TrainingArguments(
    output_dir="outputs",
    per_device_train_batch_size=1,     # Minimal batch size to protect CPU memory
    gradient_accumulation_steps=4,     # Simulates a larger batch size safely
    num_train_epochs=1,
    logging_steps=10,
    save_steps=50,
    use_cpu=True,                      # Explicitly forces HF to bypass checking for CUDA GPUs
    fp16=False,                        # native mixed-precision training requires GPU CUDA
)

# 5. Initialize Trainer & Run
trainer = Trainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=tokenized_ds,
    args=training_args,
    data_collator=data_collator,
)

print("Starting training on CPU...")
try:
    trainer.train()
    print("Training Complete!")
    # Save your LoRA adapters locally
    model.save_pretrained("outputs/final_lora_weights")
    tokenizer.save_pretrained("outputs/final_lora_weights")
except Exception as e:
    print(f"Training failed: {e}")


#Task: Remove unsloth and integrate huggin face into pipeline to run on CPU