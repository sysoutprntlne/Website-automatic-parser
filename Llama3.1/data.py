# Install dependencies as needed:
# pip install kagglehub[pandas-datasets]

import kaggle
import kagglehub
from kagglehub import KaggleDatasetAdapter
import pandas as pd
import csv

from tokenizers import (
    decoders,
    models,
    normalizers,
    pre_tokenizers,
    processors,
    trainers,
    Tokenizer,
)

# Download latest version


#== DATA FOR TOKENIZER TRAINING ==

# Set the path to the file you'd like to load
file_path = "lexor_dataset_conversations.csv"


# Load the latest version
df = kagglehub.load_dataset(
KaggleDatasetAdapter.PANDAS,
"zlatan599/lexor-2026",
"150k_conversations_14M_tokens/150kconversations/lexor_dataset_conversations.csv"

)

#View the default number of rows (first 5 rows)

print(df.columns)

text_example = df["text"].iloc[1000]

#== TOKENIZER BUILD ==


tokenizer = Tokenizer(models.BPE())

tokenizer.normalizer = normalizers.BertNormalizer()

print(tokenizer.normalizer.normalize_str(text_example))

#Find a way to insert data into tokenizer