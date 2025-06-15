

from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import json

"""
pip install nltk scikit-learn 
"""

# #### Text Cleaning & Preprocessing (per paragraph)
# * Lowercase, remove punctuation
# * Tokenize (split into words)
# * Remove stopwords (e.g., "the", "is")
# * Lemmatize or stem (reduce to base forms)
# Use Spark NLP here.

def preprocess_paragraphs(
        paragraphs: list
    ) -> list:
    """
    Preprocess paragraphs by cleaning text, tokenizing, removing stopwords, and lemmatizing/stemming.
    
    Args:
        paragraphs (list): List of paragraphs with 'text' field.
        
    Returns:
        list: Cleaned paragraphs.
    """
    cleaned_paragraphs = []
    for paragraph in paragraphs:
        # Lowercase
        text = paragraph["text"].lower()
        # Remove punctuation
        text = ''.join(char for char in text if char.isalnum() or char.isspace())
        # Tokenize
        tokens = text.split()
        # Remove stopwords (example list)
        stopwords_set = {"the", "is", "and", "to", "a"}
        tokens = [word for word in tokens if word not in stopwords_set]
        # Lemmatize or stem (example: using simple stemming)
        tokens = [word[:-1] if word.endswith("s") else word for word in tokens]
        
        paragraph["text"] = ' '.join(tokens)
        cleaned_paragraphs.append(paragraph)
    
    return cleaned_paragraphs


# Save cleaned paragraphs
# with open("output/podcast_joe_segmented_cleaned.json", "w") as json_file:
#     json.dump(paragraphs_cleaned, json_file, indent=4)