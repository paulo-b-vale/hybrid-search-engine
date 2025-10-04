from typing import List, Dict, Any, Optional, TypedDict

class SearchState(TypedDict):
    """Shared state across all workflow nodes"""
    # Input
    query: str
    index_name: str
    search_method: str
    num_results: int
    
    # Search results and processing
    search_results: List[Dict[str, Any]]
    processed_context: str
    context_metadata: Dict[str, Any]
    
    # Analysis results
    content_analysis: Dict[str, Any]
    similarity_analysis: Dict[str, Any]
    answer_data: Dict[str, Any]
    
    # Quality control
    validation_results: Dict[str, Any]
    quality_score: float
    retry_count: int
    
    # Workflow tracking
    messages: List[str]
    current_step: str
    error: Optional[str]
    
    # Performance metrics
    step_times: Dict[str, float]
    total_tokens: int
    cost_estimate: float