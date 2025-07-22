"""Main entry point for MS MARCO evaluation."""

import logging
from config.settings import CONFIG
from utils.logging import setup_logging
from data.loader import MSMarcoDataLoader
from models.dense_retrieval import DenseRetrieval
from indexing.dense_indexer import DenseIndexer
from indexing.sparse_indexer import SparseIndexer
from search.dense_search import DenseSearcher
from search.sparse_search import SparseSearcher
from search.hybrid_search import HybridSearcher
from evaluation.evaluator import MSMarcoEvaluator

logger = setup_logging()

def main():
    """Main function for MS MARCO evaluation."""
    logger.info("="*80)
    logger.info("STARTING MS MARCO EVALUATION SYSTEM")
    logger.info("="*80)

    try:
        # Initialize data loader
        data_loader = MSMarcoDataLoader(CONFIG.SAVE_DIR)
        data_loader.load_full_msmarco_data()
        
        # Initialize models and indexers
        dense_model = DenseRetrieval(CONFIG.MODEL_NAME)
        dense_indexer = DenseIndexer(CONFIG.SAVE_DIR)
        sparse_indexer = SparseIndexer()
        
        # Build indices
        dense_indexer.build_index(data_loader.documents)
        sparse_indexer.build_index(data_loader.tokenized_docs)
        
        # Initialize searchers
        dense_searcher = DenseSearcher(dense_indexer, dense_model)
        sparse_searcher = SparseSearcher(sparse_indexer)
        hybrid_searcher = HybridSearcher(dense_searcher, sparse_searcher)
        
        # Run evaluation
        evaluator = MSMarcoEvaluator(
            hybrid_searcher,
            data_loader.dev_queries,
            data_loader.qrels
        )
        
        results = evaluator.evaluate()
        evaluator.print_results(results)
        
    except KeyboardInterrupt:
        logger.info("\nEvaluation interrupted by user")
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
