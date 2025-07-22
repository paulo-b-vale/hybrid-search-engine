"""Text preprocessing utilities."""

import re
from typing import List

def preprocess_text(text: str) -> List[str]:
    """Enhanced text preprocessing for BM25."""
    if not text:
        return []

    # Remove special characters and convert to lowercase
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Split and filter tokens
    tokens = [token for token in text.split() if len(token) >= 2 and len(token) <= 20]
    return tokens

def safe_text_processing(text: str) -> str:
    """Safely process text to handle encoding issues."""
    try:
        # Handle potential encoding issues
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32)
        return text
    except Exception as e:
        return ""
