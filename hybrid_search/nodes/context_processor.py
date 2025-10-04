import time
from typing import Dict, Any, List
from utils.token_counter import TokenCounter
from config.settings import SearchConfig

# Try to import DSPy and LlamaIndex (optional dependencies)
try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    print("⚠️ DSPy not available. Using fallback context processing.")

try:
    from llama_index.core import Document, VectorStoreIndex
    from llama_index.core.node_parser import TokenTextSplitter
    from llama_index.core.response_synthesizers import get_response_synthesizer
    from llama_index.core.query_engine import RetrieverQueryEngine
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    print("⚠️ LlamaIndex not available. Using fallback context processing.")

class ContextProcessor:
    """DSPy-powered context processing and window management"""
    
    def __init__(self, config: SearchConfig):
        self.config = config
        self.token_counter = TokenCounter()
        
        # Initialize DSPy if available
        if DSPY_AVAILABLE:
            self.context_optimizer = ContextOptimizer()
        else:
            self.context_optimizer = None
        
        # LlamaIndex components if available
        if LLAMAINDEX_AVAILABLE:
            self.text_splitter = TokenTextSplitter(
                chunk_size=config.max_context_tokens // 4,  # Conservative chunking
                chunk_overlap=config.context_overlap
            )
        else:
            self.text_splitter = None
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process method for LangGraph compatibility"""
        return self(state)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process context with DSPy optimization"""
        step_start = time.time()
        
        state["current_step"] = "context_processing"
        state["messages"].append("🔧 Context Processor: Optimizing context window...")
        
        if not state.get("search_results"):
            state["processed_context"] = ""
            state["context_metadata"] = {}
            state["step_times"]["context_processing"] = time.time() - step_start
            return state
        
        try:
            # Extract documents
            documents = []
            for i, result in enumerate(state["search_results"]):
                doc = Document(
                    text=result['_source']['passage_text'],
                    metadata={
                        'source_id': result['_id'],
                        'score': result['_score'],
                        'index': i
                    }
                ) if LLAMAINDEX_AVAILABLE else {
                    'text': result['_source']['passage_text'],
                    'metadata': {
                        'source_id': result['_id'],
                        'score': result['_score'],
                        'index': i
                    }
                }
                documents.append(doc)
            
            # Use DSPy to optimize context selection if available
            if self.context_optimizer:
                optimized_context = self.context_optimizer(
                    query=state["query"],
                    documents=documents,
                    max_tokens=self.config.max_context_tokens
                )
            else:
                optimized_context = self._simple_context_selection(
                    documents, 
                    self.config.max_context_tokens
                )
            
            # Process with LlamaIndex for better chunking if available
            if LLAMAINDEX_AVAILABLE:
                processed_context = self._process_with_llamaindex(
                    optimized_context, 
                    state["query"]
                )
            else:
                processed_context = self._fallback_context_processing(
                    optimized_context["selected_passages"]
                )
            
            state["processed_context"] = processed_context["context"]
            state["context_metadata"] = processed_context["metadata"]
            
            state["messages"].append(
                f"🔧 Context Processor: Optimized to {processed_context['metadata']['total_tokens']} tokens"
            )
            
        except Exception as e:
            state["error"] = f"Context processing error: {str(e)}"
            state["processed_context"] = self._fallback_context_processing(state["search_results"])
            state["messages"].append(f"❌ Context Processor: Error - {str(e)}")
        
        state["step_times"]["context_processing"] = time.time() - step_start
        return state
    
    def _process_with_llamaindex(self, context_data: Dict, query: str) -> Dict[str, Any]:
        """Use LlamaIndex for sophisticated context processing"""
        
        # Create documents from optimized context
        documents = []
        for item in context_data["selected_passages"]:
            doc = Document(
                text=item["text"],
                metadata=item["metadata"]
            )
            documents.append(doc)
        
        # Create index and query engine
        index = VectorStoreIndex.from_documents(documents)
        
        # Get response synthesizer with context window management
        response_synthesizer = get_response_synthesizer(
            response_mode="tree_summarize",  # Good for long contexts
            use_async=False
        )
        
        # Create query engine
        query_engine = RetrieverQueryEngine(
            retriever=index.as_retriever(similarity_top_k=5),
            response_synthesizer=response_synthesizer
        )
        
        # Prepare context for LLM
        context_parts = []
        total_tokens = 0
        
        for item in context_data["selected_passages"]:
            tokens = self.token_counter.count_tokens(item["text"])
            if total_tokens + tokens <= self.config.max_context_tokens:
                context_parts.append(f"[Source {item['metadata']['index'] + 1}] {item['text']}")
                total_tokens += tokens
            else:
                break
        
        return {
            "context": "\n\n".join(context_parts),
            "metadata": {
                "total_tokens": total_tokens,
                "num_sources": len(context_parts),
                "optimization_score": context_data.get("score", 0.0)
            }
        }
    
    def _simple_context_selection(self, documents: List, max_tokens: int) -> Dict[str, Any]:
        """Simple context selection without DSPy"""
        selected = []
        total_tokens = 0
        
        # Sort by score
        sorted_docs = sorted(documents, 
                           key=lambda x: x.metadata.get('score', 0) if hasattr(x, 'metadata') else x['metadata'].get('score', 0), 
                           reverse=True)
        
        for doc in sorted_docs:
            if hasattr(doc, 'text'):
                doc_text = doc.text
                doc_tokens = self.token_counter.count_tokens(doc_text)
            else:
                doc_text = doc['text']
                doc_tokens = self.token_counter.count_tokens(doc_text)
            
            if total_tokens + doc_tokens <= max_tokens:
                selected.append({
                    "text": doc_text,
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else doc['metadata']
                })
                total_tokens += doc_tokens
            else:
                break
        
        return {
            "selected_passages": selected,
            "score": len(selected) / len(documents) if documents else 0
        }
    
    def _fallback_context_processing(self, search_results: List[Dict]) -> Dict[str, Any]:
        """Fallback context processing without DSPy/LlamaIndex"""
        context_parts = []
        total_tokens = 0
        
        for i, result in enumerate(search_results[:5]):
            text = result['_source']['passage_text']
            tokens = self.token_counter.count_tokens(text)
            
            if total_tokens + tokens <= self.config.max_context_tokens:
                context_parts.append(f"[Source {i + 1}] {text}")
                total_tokens += tokens
            else:
                # Truncate text to fit
                remaining_tokens = self.config.max_context_tokens - total_tokens
                if remaining_tokens > 100:  # Only add if meaningful space left
                    truncated_text = text[:remaining_tokens * 4]  # Rough char estimation
                    context_parts.append(f"[Source {i + 1}] {truncated_text}...")
                break
        
        return {
            "context": "\n\n".join(context_parts),
            "metadata": {
                "total_tokens": total_tokens,
                "num_sources": len(context_parts),
                "optimization_score": 0.0
            }
        }


if DSPY_AVAILABLE:
    class ContextOptimizer(dspy.Module):
        """DSPy module for intelligent context optimization"""
        
        def __init__(self):
            super().__init__()
            self.context_selector = dspy.Predict("query, documents -> selected_passages, reasoning")
        
        def forward(self, query: str, documents: List, max_tokens: int):
            """Select and optimize context using DSPy"""
            
            # Prepare documents summary for DSPy
            doc_summaries = []
            for i, doc in enumerate(documents):
                if hasattr(doc, 'text'):
                    doc_text = doc.text
                    doc_metadata = doc.metadata
                else:
                    doc_text = doc['text']
                    doc_metadata = doc['metadata']
                
                summary = {
                    "id": i,
                    "text": doc_text[:200] + "..." if len(doc_text) > 200 else doc_text,
                    "metadata": doc_metadata,
                    "length": len(doc_text)
                }
                doc_summaries.append(summary)
            
            # Use DSPy to select best passages
            try:
                result = self.context_selector(
                    query=query,
                    documents=str(doc_summaries)
                )
                
                # Parse DSPy result and select passages
                selected_passages = self._parse_selection_result(result, documents, max_tokens)
                
            except Exception as e:
                # Fallback to simple selection
                selected_passages = self._simple_selection(documents, max_tokens)
            
            return {
                "selected_passages": selected_passages,
                "score": len(selected_passages) / len(documents) if documents else 0
            }
        
        def _parse_selection_result(self, result, documents: List, max_tokens: int):
            """Parse DSPy selection result"""
            # This would implement parsing logic based on DSPy output format
            # For now, implement a smart selection based on scores and relevance
            return self._smart_selection(documents, max_tokens)
        
        def _smart_selection(self, documents: List, max_tokens: int):
            """Smart passage selection based on scores and diversity"""
            selected = []
            total_tokens = 0
            
            # Sort by score (assuming it's in metadata)
            sorted_docs = sorted(documents, 
                               key=lambda x: x.metadata.get('score', 0) if hasattr(x, 'metadata') else x['metadata'].get('score', 0), 
                               reverse=True)
            
            for doc in sorted_docs:
                if hasattr(doc, 'text'):
                    doc_text = doc.text
                    doc_metadata = doc.metadata
                else:
                    doc_text = doc['text']
                    doc_metadata = doc['metadata']
                
                doc_tokens = len(doc_text) // 4  # Rough estimation
                if total_tokens + doc_tokens <= max_tokens:
                    selected.append({
                        "text": doc_text,
                        "metadata": doc_metadata
                    })
                    total_tokens += doc_tokens
                else:
                    break
            
            return selected
        
        def _simple_selection(self, documents: List, max_tokens: int):
            """Simple fallback selection"""
            selected = []
            total_tokens = 0
            
            for doc in documents:
                if hasattr(doc, 'text'):
                    doc_text = doc.text
                    doc_metadata = doc.metadata
                else:
                    doc_text = doc['text']
                    doc_metadata = doc['metadata']
                
                doc_tokens = len(doc_text) // 4
                if total_tokens + doc_tokens <= max_tokens:
                    selected.append({
                        "text": doc_text,
                        "metadata": doc_metadata
                    })
                    total_tokens += doc_tokens
                else:
                    break
            
            return selected 