"""Sparse (BM25) search implementation."""

import numpy as np
import logging
from typing import List, Tuple
from ..indexing.sparse_indexer import SparseIndexer
from ..data.preprocessor import preprocess_text
from ..config.settings import CONFIG

logger = logging.getLogger(__name__)

class SparseSearcher:
    def __init__(self, indexer: SparseIndexer):
        self.indexer = indexer

    def search(self, query: str, k: int = CONFIG.DENSE_K) -> List[Tuple[int, float]]:
        """Search using BM25."""
        # Preprocess query
        query_tokens = preprocess_text(query)
        
        # Get BM25 scores
        scores = self.indexer.bm25.get_scores(query_tokens)
        
        # Get top k documents
        top_k_indices = np.argsort(-scores)[:k]
        top_k_scores = scores[top_k_indices]
        
        # Return (doc_idx, score) pairs
        return list(zip(top_k_indices.tolist(), top_k_scores.tolist()))
