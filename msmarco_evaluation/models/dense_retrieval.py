"""Dense retrieval model implementation."""

from sentence_transformers import SentenceTransformer
import torch
import numpy as np
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class DenseRetrieval:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self._load_model()

    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.model.to(device)
            logger.info(f"Model loaded successfully on {device}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def encode(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> np.ndarray:
        """Encode texts to dense vectors."""
        if not self.model:
            raise RuntimeError("Model not loaded")
            
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
