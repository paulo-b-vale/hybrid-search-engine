"""Hybrid search implementation combining dense and sparse retrieval."""

import numpy as np
from typing import List, Tuple
import logging
from .dense_search import DenseSearcher
from .sparse_search import SparseSearcher
from ..config.settings import CONFIG

logger = logging.getLogger(__name__)

class HybridSearcher:
    def __init__(self, dense_searcher: DenseSearcher, sparse_searcher: SparseSearcher):
        self.dense_searcher = dense_searcher
        self.sparse_searcher = sparse_searcher

    def search(self, 
              query: str, 
              k: int = CONFIG.HYBRID_K, 
              alpha: float = CONFIG.HYBRID_ALPHA,
              candidate_k: int = CONFIG.HYBRID_CANDIDATE_K) -> List[Tuple[int, float]]:
        """
        Perform hybrid search combining dense and sparse retrieval.
        
        Args:
            query: Search query
            k: Number of results to return
            alpha: Weight for dense scores (1-alpha for sparse)
            candidate_k: Number of candidates to consider from each method
        """
        # Get results from both methods
        dense_results = self.dense_searcher.search(query, k=candidate_k)
        sparse_results = self.sparse_searcher.search(query, k=candidate_k)

        # Normalize scores
        dense_scores = {idx: score for idx, score in dense_results}
        sparse_scores = {idx: score for idx, score in sparse_results}

        # Combine unique document IDs
        all_ids = set(dense_scores.keys()) | set(sparse_scores.keys())

        # Calculate hybrid scores
        hybrid_scores = []
        for doc_id in all_ids:
            dense_score = dense_scores.get(doc_id, 0)
            sparse_score = sparse_scores.get(doc_id, 0)
            
            # Combine scores
            hybrid_score = (alpha * dense_score) + ((1 - alpha) * sparse_score)
            hybrid_scores.append((doc_id, hybrid_score))

        # Sort by score and return top k
        hybrid_scores.sort(key=lambda x: x[1], reverse=True)
        return hybrid_scores[:k]
