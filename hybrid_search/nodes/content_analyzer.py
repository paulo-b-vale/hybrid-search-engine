import time
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from utils.serialization import convert_numpy_values

class ContentAnalyzerNode:
    """Content analyzer agent - analyzes content patterns"""
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process method for LangGraph compatibility"""
        return self(state)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content patterns in search results"""
        step_start = time.time()
        
        state["current_step"] = "content_analysis"
        state["messages"].append("🔬 Content Analyzer: Analyzing document content...")
        
        if not state.get("search_results"):
            state["content_analysis"] = {}
            state["step_times"]["content_analysis"] = time.time() - step_start
            return state
        
        try:
            results = state["search_results"]
            texts = [result['_source']['passage_text'] for result in results]
            scores = [result['_score'] for result in results]
            
            # Content statistics
            text_lengths = [len(text) for text in texts]
            word_counts = [len(text.split()) for text in texts]
            
            # Topic extraction (simple keyword frequency)
            all_words = ' '.join(texts).lower().split()
            word_freq = {}
            for word in all_words:
                if len(word) > 3 and word.isalpha():  # Skip short words and numbers
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Content diversity analysis
            unique_words = set(all_words)
            total_words = len(all_words)
            diversity_ratio = len(unique_words) / total_words if total_words > 0 else 0
            
            content_analysis = {
                'num_documents': len(results),
                'avg_text_length': float(np.mean(text_lengths)),
                'avg_word_count': float(np.mean(word_counts)),
                'score_stats': {
                    'min': float(min(scores)),
                    'max': float(max(scores)),
                    'mean': float(np.mean(scores)),
                    'std': float(np.std(scores))
                },
                'top_keywords': top_keywords,
                'content_diversity': float(diversity_ratio),
                'total_unique_words': len(unique_words),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Ensure all values are serializable
            state["content_analysis"] = convert_numpy_values(content_analysis)
            
            state["messages"].append(f"📊 Content Analyzer: Analyzed {len(results)} documents")
            state["messages"].append(f"🔑 Top themes: {', '.join([kw[0] for kw in top_keywords[:3]])}")
            
        except Exception as e:
            state["error"] = f"Content analysis error: {str(e)}"
            state["content_analysis"] = {}
            state["messages"].append(f"❌ Content Analyzer: Error - {str(e)}")
        
        state["step_times"]["content_analysis"] = time.time() - step_start
        return state 