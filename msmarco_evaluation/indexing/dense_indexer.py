"""Dense index building and management."""

import faiss
import numpy as np
import os
import torch
import logging
from typing import Optional
from ..models.dense_retrieval import DenseRetrieval
from ..config.settings import CONFIG

logger = logging.getLogger(__name__)

class DenseIndexer:
    def __init__(self, save_dir: str):
        self.save_dir = save_dir
        self.dense_index: Optional[faiss.Index] = None
        self.embeddings: Optional[np.ndarray] = None
        self.model = DenseRetrieval(CONFIG.MODEL_NAME)

    def build_index(self, documents: list, batch_size: int = 32):
        """Build dense FAISS index."""
        logger.info("Building dense FAISS index...")

        embeddings_path = os.path.join(self.save_dir, 'embeddings.npy')
        index_path = os.path.join(self.save_dir, 'faiss_index.bin')

        # Try to load existing embeddings and index
        if os.path.exists(embeddings_path) and os.path.exists(index_path):
            self.embeddings = np.load(embeddings_path)
            self.dense_index = faiss.read_index(index_path)
            logger.info("Loaded existing index and embeddings")
            return

        # Generate embeddings
        self.embeddings = self.model.encode(documents, batch_size=batch_size)

        # Save embeddings
        np.save(embeddings_path, self.embeddings)

        # Build index
        embedding_dim = self.embeddings.shape[1]
        self.dense_index = faiss.IndexFlatIP(embedding_dim)
        if torch.cuda.is_available():
            logger.info("Using GPU for FAISS index")
            res = faiss.StandardGpuResources()
            self.dense_index = faiss.index_cpu_to_gpu(res, 0, self.dense_index)

        self.dense_index.add(self.embeddings)
        faiss.write_index(faiss.index_gpu_to_cpu(self.dense_index) 
                         if torch.cuda.is_available() 
                         else self.dense_index, 
                         index_path)
        
        logger.info("Dense index built and saved successfully")
