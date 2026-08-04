# Install dependencies as needed:
# pip install kagglehub[pandas-datasets]
from tokenizers.processors import TemplateProcessing
import kagglehub
from kagglehub import KaggleDatasetAdapter
from tokenizers import (
    models,
    normalizers,
    pre_tokenizers,
    trainers,
    Tokenizer,
    
    
)

# Download latest version


#== DATA FOR TOKENIZER TRAINING ==

# Load the latest version
df = kagglehub.load_dataset(
KaggleDatasetAdapter.PANDAS,
"zlatan599/lexor-2026",
"150k_conversations_14M_tokens/150kconversations/lexor_dataset_conversations.csv"

)

#View the default number of rows (first 5 rows)


#== TOKENIZER BUILD ==

#normalizer
tokenizer = Tokenizer(models.BPE())
tokenizer.normalizer = normalizers.BertNormalizer()

#Pre-tokenize
tokenizer.pre_tokenizer = pre_tokenizers.BertPreTokenizer()



tokenizer.post_processor = TemplateProcessing(
    single="[CLS] $A [SEP]",
    pair="[CLS] $A [SEP] $B:1 [SEP]:1",
    special_tokens=[("[CLS]", 1), ("[SEP]", 2)],
)

#pre-training tokenizer

trainer = trainers.BpeTrainer(
    vocab_size=25000,
    special_tokens=[
        "[PAD]",
        "[UNK]",
        "[CLS]",
        "[SEP]",
        "[MASK]"
    ]
)

#a function that calls batches to create streaming

def batch_tokenizer_training():
    
    batch_size = 1000
    for i in range(0, len(df), batch_size):
        yield df["text"].iloc[i:i+batch_size].tolist()
        
        
        
        #it gets smaller every time
tokenizer.train_from_iterator(batch_tokenizer_training(), trainer=trainer, length = len(df))
        
        
        
tokenizer.save("Llama3.1/BPE-tokens.json")
#total dataset size is 176154

def get_tokenizer():
    return tokenizer.from_file("/Users/admin/code 2026/Website-automatic-parser/Llama3.1/BPE-tokens.json")


