# 🤖 Autonomous AI Agent System for Hybrid Search & Synthesis

## A Multi-Agent System that Powers a Sophisticated Q&A Application

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![FAISS](https://img.shields.io/badge/FAISS-IVF--Optimized-green)](https://github.com/facebookresearch/faiss)
[![Transformers](https://img.shields.io/badge/🤗-Transformers-yellow)](https://huggingface.co/transformers/)
[![Thesis Grade](https://img.shields.io/badge/University%20Thesis-10%2F10-gold)](#)
[![Presentation Grade](https://img.shields.io/badge/Thesis%20Presentation-10%2F10-brightgreen)](#)

---

### 🚀 Live Application Demo

This video shows the final application in action. The system uses a team of six specialized AI agents to process a user's query and generate a comprehensive, source-backed answer.

[![Watch the Demo Video](<img width="1366" height="646" alt="image" src="https://github.com/user-attachments/assets/8363b51d-803b-4d63-beca-5c81be09a87a" />
)](URL_OF_YOUR_VIDEO)

**[Watch the 1:52 minute video demo here](URL_OF_YOUR_VIDEO)**

---

### 🎯 Project Overview

**From Thesis to Application**: This project evolved from my **Thesis I (TCC1) at the Federal University of Piauí (UFPI)**, where both the written article and the final presentation earned a **perfect 10/10 grade**. The work has since been expanded into this fully-functional, multi-agent Q&A system.

This is not just a search index; it's a sophisticated **multi-agent AI system** designed to deliver intelligent and reliable answers. When a user asks a question, a workflow is orchestrated between six specialized agents, each handling a critical part of the process from retrieval to final answer synthesis.

The system's foundation is a powerful **hybrid retrieval engine** that fuses dense (semantic) and sparse (lexical) search, achieving state-of-the-art performance on the 8.8M+ document MS MARCO dataset.

---

### 🏗️ The Six-Agent Architecture

The system's intelligence is distributed across six collaborative agents. I've created a live, interactive webpage to visualize and explain the entire workflow and the technologies used.

[![Interactive Architecture Website](URL_to_your_screenshot.png)](https://your-username.github.io/your-repo-name/)

**[Click here to explore the live, interactive diagram](https://your-username.github.io/your-repo-name/)**

#### Agent Roles:
1.  **🎯 The Coordinator Agent**: Analyzes the initial query to understand user intent and plans the optimal execution strategy for the other agents.
2.  **🔍 The Retrieval Agent**: Executes the hybrid search plan, querying the high-performance FAISS and BM25 indices to find the most relevant source documents.
3.  **🔬 The Content Analyzer Agent**: Scans the retrieved documents to identify and extract key themes and concepts, providing a summarized context.
4.  **🔧 The Context Processor Agent**: intelligently selects and condenses the most critical information from the analyzed content, preparing a perfectly optimized context for the language model.
5.  **🧠 The Answer Synthesizer Agent**: Takes the optimized context and uses a powerful generative model (like Gemini) to formulate a comprehensive, well-written, and coherent answer.
6.  **✅ The Quality Validator Agent**: Assesses the generated answer for quality, relevance, and factual consistency against the source documents, assigning a final quality score.

---

### ⚡ Core Engine: The Hybrid Retrieval System

The agents are powered by a best-in-class retrieval engine that was the focus of my 10/10 graded thesis. It combines a custom-optimized BM25 with a highly-tuned FAISS IVF index for semantic search.

#### Performance Metrics (on 6,980 MS MARCO Dev Queries)

| Method          | MAP ↑      | Recall@10 ↑ | MRR@10 ↑   | NDCG@10 ↑  | Latency (s) ↓ |
| :-------------- | :--------: | :---------: | :--------: | :--------: | :-----------: |
| **Dense (FAISS)** | **95.14%** | **99.24%** | **95.29%** | **96.20%** | 55.8          |
| **Sparse (BM25)** | 81.24%   | 91.43%    | 81.61%   | 83.73%   | 59.2          |
| **Hybrid Fusion** | **93.25%** | **99.28%** | **93.50%** | **94.82%** | 127.5         |

---

### 🛠️ About This Code Repository

Please note: For proprietary reasons, this repository does **not** contain the full codebase for the multi-agent orchestration logic or the frontend application.

The code provided here is a clean, production-ready implementation of the **core hybrid retrieval engine** that powers the **Retrieval Agent**. It contains the complete, high-performance FAISS and BM25 systems developed for my thesis, demonstrating the foundational layer upon which the full application is built.

---

### 🚀 Technical Skills Demonstrated

#### AI Agent & System Design
- Autonomous Agent Workflows
- Multi-Agent Collaboration & Orchestration
- Generative AI Synthesis & Validation
- Complex System Architecture

#### Machine Learning & NLP
- Transformer-based Semantic Embeddings
- Information Retrieval Metrics (MAP, MRR, NDCG)
- Large-scale Text Processing (8.8M+ Docs)
- Neural Ranking and Fusion Techniques

#### High-Performance Computing & Software Engineering
- FAISS Vector Search Optimization
- Memory-Efficient Batch Processing & Caching
- GPU Acceleration & Resource Management
- Production-Ready Python & API Design

---

### 🎓 Academic Context & Future Work

This project represents comprehensive research and practical application in AI, demonstrating:
- **State-of-the-Art Integration**: Combining retrieval and generative AI.
- **Rigorous Evaluation**: Thesis work validated on standard benchmarks.
- **Technical Innovation**: A novel, efficient multi-agent workflow.

Future enhancements include integrating neural re-rankers, automated query expansion, and scaling the system in a distributed environment.

---

*This project showcases a deep, end-to-end capability in designing, building, and evaluating complex AI systems—from foundational retrieval algorithms to sophisticated agentic applications.*
