"""Data loading and management utilities."""

import os
import pickle
import logging
from typing import Dict, List, Tuple
from datasets import load_dataset
import ir_datasets
from ..config.settings import CONFIG

logger = logging.getLogger(__name__)

class MSMarcoDataLoader:
    def __init__(self, save_dir: str):
        self.save_dir = save_dir
        self.documents: List[str] = []
        self.doc_ids: List[str] = []
        self.doc_id_to_index: Dict[str, int] = {}
        self.tokenized_docs: List[List[str]] = []
        self.dev_queries: Dict[str, str] = {}
        self.qrels: Dict[str, Dict[str, int]] = {}
        
        os.makedirs(save_dir, exist_ok=True)

    def load_full_msmarco_data(self):
        """Load the FULL MS MARCO dataset."""
        logger.info("Loading FULL MS MARCO dataset...")

        # Check for cached data
        if self._load_cached_data():
            return

        try:
            # Try loading with HuggingFace datasets
            self._load_with_hf_datasets()
        except Exception as e:
            logger.warning(f"Failed to load with HuggingFace: {e}")
            # Fallback to ir_datasets
            self._load_with_ir_datasets()

        # Save the loaded data
        self._save_all_data()

    def _load_with_hf_datasets(self):
        """Load dataset using HuggingFace datasets."""
        dataset = load_dataset("ms_marco", "v2.1")
        
        # Load documents
        for idx, doc in enumerate(dataset["train"]):
            self.documents.append(doc["passage"])
            self.doc_ids.append(str(doc["id"]))
            self.doc_id_to_index[str(doc["id"])] = idx

        # Load dev queries and relevance judgments
        for query in dataset["validation"]:
            qid = str(query["query_id"])
            self.dev_queries[qid] = query["query"]
            self.qrels[qid] = {str(doc_id): 1 for doc_id in query["relevant_passages"]}

    def _load_with_ir_datasets(self):
        """Load dataset using ir_datasets as fallback."""
        dataset = ir_datasets.load("msmarco-passage/train")
        
        # Load documents
        for idx, doc in enumerate(dataset.docs_iter()):
            self.documents.append(doc.text)
            self.doc_ids.append(str(doc.doc_id))
            self.doc_id_to_index[str(doc.doc_id)] = idx

        # Load dev queries and relevance judgments
        dev_dataset = ir_datasets.load("msmarco-passage/dev")
        for query in dev_dataset.queries_iter():
            self.dev_queries[str(query.query_id)] = query.text

        for qrel in dev_dataset.qrels_iter():
            qid = str(qrel.query_id)
            if qid not in self.qrels:
                self.qrels[qid] = {}
            self.qrels[qid][str(qrel.doc_id)] = qrel.relevance

    def _load_cached_data(self) -> bool:
        """Load cached data if available."""
        docs_path = os.path.join(self.save_dir, 'documents.pkl')
        queries_path = os.path.join(self.save_dir, 'dev_queries.pkl')
        qrels_path = os.path.join(self.save_dir, 'qrels.pkl')

        if all(os.path.exists(p) for p in [docs_path, queries_path, qrels_path]):
            try:
                with open(docs_path, 'rb') as f:
                    docs_data = pickle.load(f)
                    self.documents = docs_data['documents']
                    self.doc_ids = docs_data['doc_ids']
                    self.doc_id_to_index = docs_data['doc_id_to_index']
                    
                with open(queries_path, 'rb') as f:
                    self.dev_queries = pickle.load(f)
                    
                with open(qrels_path, 'rb') as f:
                    self.qrels = pickle.load(f)
                    
                logger.info("Loaded cached dataset")
                return True
            except Exception as e:
                logger.error(f"Error loading cached data: {e}")
                return False
        return False

    def _save_all_data(self):
        """Save all loaded data to cache."""
        try:
            docs_data = {
                'documents': self.documents,
                'doc_ids': self.doc_ids,
                'doc_id_to_index': self.doc_id_to_index
            }
            with open(os.path.join(self.save_dir, 'documents.pkl'), 'wb') as f:
                pickle.dump(docs_data, f)
            with open(os.path.join(self.save_dir, 'dev_queries.pkl'), 'wb') as f:
                pickle.dump(self.dev_queries, f)
            with open(os.path.join(self.save_dir, 'qrels.pkl'), 'wb') as f:
                pickle.dump(self.qrels, f)
            logger.info("Saved dataset to cache")
        except Exception as e:
            logger.error(f"Error saving dataset to cache: {e}")
