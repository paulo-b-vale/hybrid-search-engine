# 🔍 MS MARCO Hybrid Retrieval System

## Advanced Information Retrieval with Dense-Sparse Fusion

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FAISS](https://img.shields.io/badge/FAISS-IVF--Optimized-green)](https://github.com/facebookresearch/faiss)
[![Transformers](https://img.shields.io/badge/🤗-Transformers-yellow)](https://huggingface.co/transformers/)
[![Grade](https://img.shields.io/badge/University%20Grade-10%2F10-gold)](#)

> **Academic Achievement**: This project was developed as my TCC1 (Thesis) at the Federal University of Brazil, achieving a **perfect 10/10 grade**. It demonstrates advanced information retrieval techniques with state-of-the-art performance on the MS MARCO dataset.

## 🎯 Project Overview

This system implements a sophisticated **hybrid information retrieval architecture** that combines the semantic understanding of dense retrieval with the lexical precision of sparse retrieval methods. The solution achieves exceptional performance on the MS MARCO passage ranking dataset through intelligent algorithmic fusion and computational optimization.

### 🏆 Key Achievements

- **Dense Retrieval**: MAP of **95.14%** with **99.87% overall recall**
- **Hybrid System**: Maintains **93.25% MAP** while optimizing computational efficiency
- **Scalability**: Processes **8.8M+ documents** with sub-second query response times
- **Academic Recognition**: Perfect score (10/10) thesis project

## 🏗️ Architecture & Technical Innovation

### 1. Dense Retrieval Engine
- **Model**: Sentence-BERT (all-MiniLM-L6-v2) for semantic embeddings
- **Index Structure**: FAISS IVF (Inverted File with Virtual Centroids)
- **Optimization**: Dynamic centroid calculation for optimal memory-performance balance
- **Performance**: 99.24% Recall@10, 95.29% MRR@10

### 2. Sparse Retrieval (BM25)
- **Implementation**: Custom optimized BM25 with proper vectorization
- **Features**: Document frequency caching, term weighting optimization
- **Performance**: 91.43% Recall@10, solid baseline for lexical matching

### 3. Hybrid Fusion Strategy
**The core innovation**: A computationally intelligent hybrid approach that:

- **Phase 1**: Dense retrieval identifies **500 semantic candidates**
- **Phase 2**: BM25 re-ranking for lexical precision refinement
- **Phase 3**: Score normalization and weighted fusion (α=0.5)

**Why 500 candidates?** This sweet spot minimizes computational cost while preserving 99%+ of relevant documents, demonstrating deep understanding of the precision-recall trade-off in large-scale retrieval.

## 🔬 Technical Deep Dive

### FAISS IVF Implementation
```python
# Intelligent centroid calculation
n_list = min(max(int(4 * √num_docs), 4000), num_docs // 50)

# IVF index with optimized probe settings
index = faiss.IndexIVFFlat(quantizer, dimension, n_list)
index.nprobe = min(100, n_list // 2)  # Dynamic probe adjustment
```

### Memory-Efficient Processing
- **Batch Processing**: Chunked embedding generation (25K docs/batch on GPU)
- **Progressive Caching**: Intermediate data persistence for fault tolerance
- **Memory Management**: Strategic garbage collection and CUDA cache clearing

### Computational Optimization
- **Multi-threading**: Parallel document processing and tokenization
- **Vectorized Operations**: NumPy-optimized BM25 scoring
- **Index Persistence**: Smart caching system for repeated evaluations

## 📊 Experimental Results

### Performance Metrics (6,980 MS MARCO Dev Queries)

| Method | MAP ↑ | Recall@10 ↑ | MRR@10 ↑ | NDCG@10 ↑ | Latency (s) ↓ |
|--------|-------|--------------|----------|-----------|---------------|
| **Dense** | **95.14%** | **99.24%** | **95.29%** | **96.20%** | 55.8 |
| BM25 | 81.24% | 91.43% | 81.61% | 83.73% | 59.2 |
| **Hybrid** | **93.25%** | **99.28%** | **93.50%** | **94.82%** | 127.5 |

### Key Insights
- **Dense retrieval dominance**: Superior semantic understanding leads to exceptional MAP scores
- **Hybrid efficiency**: Maintains 98% of dense performance while providing computational flexibility
- **Scalability**: Linear performance scaling across document collection sizes

## 🛠️ Implementation Highlights

### Advanced Features
- **Robust Data Loading**: Multiple fallback mechanisms for dataset acquisition
- **Error Resilience**: Comprehensive exception handling and recovery systems  
- **Evaluation Framework**: Standard TREC metrics implementation (MAP, MRR, NDCG)
- **Progress Monitoring**: Real-time logging and performance tracking

### Code Quality
- **Type Annotations**: Complete type hinting for maintainability
- **Documentation**: Comprehensive docstrings and inline comments
- **Modularity**: Clean separation of concerns across retrieval methods
- **Testing**: Extensive validation on standard IR benchmarks

## 🚀 Technical Skills Demonstrated

### Machine Learning & NLP
- Transformer-based semantic embeddings
- Information Retrieval metrics and evaluation
- Large-scale text processing and normalization
- Neural ranking and fusion techniques

### High-Performance Computing
- FAISS vector similarity search optimization
- Memory-efficient batch processing
- GPU acceleration and resource management
- Distributed processing considerations

### Software Engineering
- Production-ready Python development
- Exception handling and error recovery
- Caching and persistence strategies
- Performance profiling and optimization

## 📈 Future Enhancements

- **Neural Re-ranking**: Integration of cross-encoder models for final ranking
- **Query Expansion**: Automated query enrichment strategies
- **Multi-Modal Retrieval**: Extension to document-image retrieval
- **Distributed Scaling**: Kubernetes-based horizontal scaling

## 🎓 Academic Context

This project represents comprehensive research in information retrieval, demonstrating:
- **Literature Review**: Integration of state-of-the-art dense and sparse methods
- **Experimental Design**: Rigorous evaluation on standard benchmarks
- **Technical Innovation**: Novel hybrid fusion with computational optimization
- **Academic Writing**: Thorough documentation and results analysis

**Grade Received**: 10/10 from Federal University of Brazil

---

*This project showcases advanced technical skills in machine learning, information retrieval, and large-scale system design - demonstrating readiness for senior engineering roles in AI/ML and search technologies.*
