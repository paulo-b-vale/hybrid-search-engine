"""BM25 implementation for sparse retrieval."""

import numpy as np
from collections import defaultdict
from typing import List, Dict
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

class BM25:
    """Optimized BM25 implementation with proper vectorization"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0
        self.doc_lens = []
        self.idf = {}
        self.doc_term_freqs = []

    def fit(self, corpus: List[List[str]]):
        """Fit BM25 on tokenized corpus"""
        logger.info(f"Fitting BM25 model on {len(corpus)} documents...")
        self.corpus_size = len(corpus)

        # Calculate document lengths
        self.doc_lens = [len(doc) for doc in corpus]
        self.avg_doc_len = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 0

        # Calculate term frequencies for each document
        self.doc_term_freqs = []
        df = defaultdict(int)  # document frequency

        for doc in tqdm(corpus, desc="Processing documents for BM25"):
            term_freqs = defaultdict(int)
            for term in doc:
                term_freqs[term] += 1
                df[term] += 1
            self.doc_term_freqs.append(term_freqs)

        # Calculate IDF
        for term, freq in df.items():
            self.idf[term] = np.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def get_scores(self, query: List[str]) -> np.ndarray:
        """Get BM25 scores for query against all documents"""
        scores = np.zeros(self.corpus_size)

        for term in query:
            if term not in self.idf:
                continue
                
            q_idf = self.idf[term]
            
            for idx, doc_terms in enumerate(self.doc_term_freqs):
                if term not in doc_terms:
                    continue
                    
                freq = doc_terms[term]
                doc_len = self.doc_lens[idx]
                
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
                scores[idx] += q_idf * numerator / denominator

        return scores
