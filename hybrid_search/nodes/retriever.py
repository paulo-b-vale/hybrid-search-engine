import time
import numpy as np
from typing import Dict, Any, List
from core.base_search import BaseSearchEngine

class RetrieverNode:
    """Specialized retrieval node"""
    
    def __init__(self, search_engine: BaseSearchEngine):
        self.search_engine = search_engine
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process method for LangGraph compatibility"""
        return self(state)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute retrieval based on state"""
        step_start = time.time()
        
        state["current_step"] = "retrieval"
        state["messages"].append(f"🔍 Retriever: Executing {state['search_method']} search...")
        
        try:
            # Perform search based on method
            if state["search_method"] == "vector":
                results = self.search_engine.vector_search(
                    state["index_name"], 
                    state["query"], 
                    size=state["num_results"]
                )
            elif state["search_method"] == "bm25":
                results = self.search_engine.bm25_search(
                    state["index_name"], 
                    state["query"], 
                    size=state["num_results"]
                )
            else:  # multi_stage/hybrid
                results = self.multi_stage_search(
                    state["index_name"], 
                    state["query"], 
                    final_size=state["num_results"]
                )
            
            state["search_results"] = results
            state["messages"].append(f"📄 Retriever: Found {len(results)} relevant documents")
            
            if not results:
                state["error"] = "No search results found"
                state["messages"].append("❌ Retriever: No results found for query")
            
        except Exception as e:
            state["error"] = f"Search error: {str(e)}"
            state["messages"].append(f"❌ Retriever: Error during search - {str(e)}")
            state["search_results"] = []
        
        state["step_times"]["retrieval"] = time.time() - step_start
        return state
    
    def multi_stage_search(self, index_name: str, query_text: str, final_size: int = 10):
        """Multi-stage hybrid search implementation"""
        vector_results = self.search_engine.vector_search(index_name, query_text, size=500)
        bm25_results = self.search_engine.bm25_search(index_name, query_text, size=500)
        
        if len(vector_results) == 0 and len(bm25_results) == 0:
            return []
        
        # Implement reranking logic here
        final_results = self._rerank_results(vector_results, bm25_results)
        return final_results[:final_size]
    
    def _rerank_results(self, vector_results: List[Dict], bm25_results: List[Dict], alpha: float = 0.7):
        """Implement result reranking"""
        if len(vector_results) == 0:
            return bm25_results
        if len(bm25_results) == 0:
            return vector_results
            
        # Create mapping of document ID to BM25 score and rank
        bm25_scores = {}
        bm25_ranks = {}
        max_bm25_score = max((hit['_score'] for hit in bm25_results), default=1)
        
        for rank, hit in enumerate(bm25_results):
            bm25_scores[hit['_id']] = hit['_score']
            bm25_ranks[hit['_id']] = rank + 1
        
        # Normalize and combine scores
        max_vector_score = max((hit['_score'] for hit in vector_results), default=1)
        
        # Collect all unique documents
        all_docs = {}
        
        # Add vector results
        for rank, hit in enumerate(vector_results):
            doc_id = hit['_id']
            all_docs[doc_id] = {
                'hit': hit,
                'vector_score': hit['_score'],
                'vector_rank': rank + 1,
                'bm25_score': bm25_scores.get(doc_id, 0),
                'bm25_rank': bm25_ranks.get(doc_id, len(bm25_results) + 1)
            }
        
        # Add BM25-only results
        for rank, hit in enumerate(bm25_results):
            doc_id = hit['_id']
            if doc_id not in all_docs:
                all_docs[doc_id] = {
                    'hit': hit,
                    'vector_score': 0,
                    'vector_rank': len(vector_results) + 1,
                    'bm25_score': hit['_score'],
                    'bm25_rank': rank + 1
                }
        
        # Calculate combined scores using RRF + normalized score fusion
        reranked_results = []
        k = 60  # RRF parameter
        
        for doc_id, data in all_docs.items():
            # Normalized scores
            norm_vector_score = data['vector_score'] / max_vector_score if max_vector_score > 0 else 0
            norm_bm25_score = data['bm25_score'] / max_bm25_score if max_bm25_score > 0 else 0
            
            # RRF scores
            rrf_vector = 1 / (k + data['vector_rank'])
            rrf_bm25 = 1 / (k + data['bm25_rank'])
            
            # Combined score (weighted combination of normalized scores and RRF)
            score_fusion = alpha * norm_vector_score + (1 - alpha) * norm_bm25_score
            rrf_fusion = alpha * rrf_vector + (1 - alpha) * rrf_bm25
            
            # Final combined score
            combined_score = 0.7 * score_fusion + 0.3 * rrf_fusion
            
            new_hit = data['hit'].copy()
            new_hit['_score'] = combined_score
            new_hit['_vector_score'] = data['vector_score']
            new_hit['_bm25_score'] = data['bm25_score']
            
            reranked_results.append(new_hit)
        
        reranked_results.sort(key=lambda x: x['_score'], reverse=True)
        return reranked_results 