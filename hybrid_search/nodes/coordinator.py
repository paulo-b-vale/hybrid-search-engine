import time
from typing import Dict, Any
from config.settings import SearchConfig

class CoordinatorNode:
    """Coordinator agent - orchestrates the workflow"""
    
    def __init__(self, config: SearchConfig):
        self.config = config
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process method for LangGraph compatibility"""
        return self.__call__(state)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze query and plan search strategy"""
        step_start = time.time()
        
        state["current_step"] = "coordination"
        
        # Initialize messages list if it doesn't exist
        if "messages" not in state or state["messages"] is None:
            state["messages"] = []
        
        state["messages"].append("🎯 Coordinator: Analyzing query and planning search strategy...")
        
        # Analyze query complexity and determine optimal strategy
        query_length = len(state["query"].split())
        
        # Optimize search method based on query characteristics
        if query_length <= 3 and any(char.isdigit() for char in state["query"]):
            # Short queries with numbers might benefit from exact matching
            recommended_method = "bm25"
        elif query_length > 10:
            # Long, complex queries benefit from semantic search
            recommended_method = "vector"
        else:
            # Default to hybrid for balanced queries
            recommended_method = "multi_stage"
        
        # Override user's method if they didn't specify
        if state.get("search_method") == "auto":
            state["search_method"] = recommended_method
            state["messages"].append(f"🧠 Coordinator: Recommended search method: {recommended_method}")
        
        # Initialize tracking structures
        if "step_times" not in state:
            state["step_times"] = {}
        
        state["step_times"]["coordination"] = time.time() - step_start
        state["messages"].append(f"✅ Coordinator: Strategy planned in {state['step_times']['coordination']:.2f}s")
        
        return state