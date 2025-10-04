"""Evaluation metrics implementation."""

from typing import Dict, List, Set
import numpy as np

def compute_mrr(qrels: Dict[str, Dict[str, int]], results: Dict[str, List[str]], cutoff: int = None) -> float:
    """
    Compute Mean Reciprocal Rank (MRR).
    
    Args:
        qrels: Relevance judgments {qid: {doc_id: relevance}}
        results: Retrieved results {qid: [doc_id]}
        cutoff: Consider only top-k results
    """
    rr_sum = 0.0
    query_count = 0

    for qid in qrels:
        if qid not in results:
            continue

        query_count += 1
        relevant_docs = set(qrels[qid].keys())
        
        for rank, doc_id in enumerate(results[qid][:cutoff] if cutoff else results[qid], 1):
            if doc_id in relevant_docs:
                rr_sum += 1.0 / rank
                break

    return rr_sum / query_count if query_count > 0 else 0.0

def compute_recall(qrels: Dict[str, Dict[str, int]], results: Dict[str, List[str]], cutoff: int = None) -> float:
    """
    Compute Recall@k.
    
    Args:
        qrels: Relevance judgments {qid: {doc_id: relevance}}
        results: Retrieved results {qid: [doc_id]}
        cutoff: Consider only top-k results
    """
    recall_sum = 0.0
    query_count = 0

    for qid in qrels:
        if qid not in results:
            continue

        query_count += 1
        relevant_docs = set(qrels[qid].keys())
        retrieved_docs = set(results[qid][:cutoff] if cutoff else results[qid])
        
        if len(relevant_docs) > 0:
            recall_sum += len(relevant_docs & retrieved_docs) / len(relevant_docs)

    return recall_sum / query_count if query_count > 0 else 0.0
