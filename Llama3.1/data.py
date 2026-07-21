# Install dependencies as needed:
# pip install kagglehub[pandas-datasets]
import kagglehub
from kagglehub import KaggleDatasetAdapter
import pandas


# Download latest version


#== DATA FOR TOKENIZER TRAINING ==

# Set the path to the file you'd like to load
file_path = "lexor_dataset_conversations.csv"

# Load the latest version
df = kagglehub.load_dataset
(
KaggleDatasetAdapter.PANDAS,
"zlatan599/lexor-2026",
"150k_conversations_14M_tokens/150kconversations/lexor_dataset_conversations.csv"

)

print("First 5 records:", df.head())

