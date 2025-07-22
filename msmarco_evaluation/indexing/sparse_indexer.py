"""Sparse (BM25) index building and management."""

import logging
from typing import List
from ..models.bm25 import BM25
from ..config.settings import CONFIG

logger = logging.getLogger(__name__)

class SparseIndexer:
    def __init__(self):
        self.bm25 = BM25(k1=CONFIG.BM25_K1, b=CONFIG.BM25_B)

    def build_index(self, tokenized_docs: List[List[str]]):
        """Build BM25 index from tokenized documents."""
        logger.info("Building BM25 index...")
        self.bm25.fit(tokenized_docs)
        logger.info("BM25 index built successfully")
