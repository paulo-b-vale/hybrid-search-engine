"""
Hybrid Search System with LangGraph, DSPy, and LlamaIndex

A modular search system that combines vector search, BM25, and multi-stage
hybrid search with advanced context processing and answer synthesis.
"""

__version__ = "1.0.0"
__author__ = "Hybrid Search Team"

from .workflows.langgraph_workflow import HybridSearchWorkflow
from .config.settings import SearchConfig

__all__ = ["HybridSearchWorkflow", "SearchConfig"] 