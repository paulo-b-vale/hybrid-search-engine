"""Configuration settings for MS MARCO evaluation."""

class Config:
    # Model settings
    MODEL_NAME = "all-MiniLM-L6-v2"
    
    # Data settings
    SAVE_DIR = "./msmarco_full_eval"
    BATCH_SIZE = 32
    CHUNK_SIZE = 1000
    
    # BM25 parameters
    BM25_K1 = 1.5
    BM25_B = 0.75
    
    # Search parameters
    DENSE_K = 1000
    HYBRID_K = 100
    HYBRID_ALPHA = 0.5
    HYBRID_CANDIDATE_K = 500

CONFIG = Config()
