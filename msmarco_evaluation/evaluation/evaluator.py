"""Main evaluation logic."""

import logging
from typing import Dict, List, Any
from tqdm import tqdm
from .metrics import compute_mrr, compute_recall
from ..search.hybrid_search import HybridSearcher
from ..config.settings import CONFIG

logger = logging.getLogger(__name__)

class MSMarcoEvaluator:
    def __init__(self, searcher: HybridSearcher, queries: Dict[str, str], qrels: Dict[str, Dict[str, int]]):
        self.searcher = searcher
        self.queries = queries
        self.qrels = qrels

    def evaluate(self, max_queries: int = None) -> Dict[str, Any]:
        """Run evaluation on dev queries."""
        logger.info("Starting evaluation...")
        
        results = {}
        query_ids = list(self.queries.keys())
        
        if max_queries:
            query_ids = query_ids[:max_queries]

        for qid in tqdm(query_ids, desc="Evaluating queries"):
            query = self.queries[qid]
            search_results = self.searcher.search(
                query,
                k=CONFIG.HYBRID_K,
                alpha=CONFIG.HYBRID_ALPHA
            )
            results[qid] = [str(doc_id) for doc_id, _ in search_results]

        # Compute metrics
        metrics = {
            'mrr@10': compute_mrr(self.qrels, results, cutoff=10),
            'mrr@100': compute_mrr(self.qrels, results, cutoff=100),
            'recall@100': compute_recall(self.qrels, results, cutoff=100),
            'recall@1000': compute_recall(self.qrels, results, cutoff=1000)
        }

        return metrics

    def print_results(self, metrics: Dict[str, float]):
        """Print evaluation results in a formatted way."""
        logger.info("\nEvaluation Results:")
        logger.info("-" * 40)
        for metric, value in metrics.items():
            logger.info(f"{metric:12}: {value:.4f}")
