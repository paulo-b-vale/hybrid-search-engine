import tiktoken
from typing import Optional

class TokenCounter:
    """Utility for counting tokens in text"""
    
    def __init__(self, encoding_name: str = "cl100k_base"):
        try:
            self.tokenizer = tiktoken.get_encoding(encoding_name)
        except:
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback estimation
            return len(text) // 4
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        if not self.tokenizer:
            # Rough estimation
            return text[:max_tokens * 4]
        
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return self.tokenizer.decode(truncated_tokens) 