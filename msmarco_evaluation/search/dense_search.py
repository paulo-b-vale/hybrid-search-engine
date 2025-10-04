"""Dense search implementation."""

import numpy as np
import logging
from typing import List, Tuple
from ..indexing.dense_indexer import DenseIndexer
from ..models.dense_retrieval import DenseRetrieval
from ..config.settings import CONFIG

logger = logging.getLogger(__name__)

class DenseSearcher:
    def __init__(self, indexer: DenseIndexer, retriever: DenseRetrieval):
        self.indexer = indexer
        self.retriever = retriever

    def search(self, query: str, k: int = CONFIG.DENSE_K) -> List[Tuple[int, float]]:
        """Search using dense retrieval."""
        # Encode query
        query_embedding = self.retriever.encode([query], show_progress=False)[0]
        query_embedding = np.expand_dims(query_embedding, axis=0)

        # Search in FAISS index
        scores, indices = self.indexer.dense_index.search(query_embedding, k)
        
        # Return (doc_idx, score) pairs
        return list(zip(indices[0].tolist(), scores[0].tolist()))
