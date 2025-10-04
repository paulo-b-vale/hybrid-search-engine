# Try to import LangGraph (optional dependency)
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️ LangGraph not available. Using fallback workflow.")
    StateGraph = None
    END = None

from typing import Dict, Any, Callable
import logging
import time

# Use absolute imports instead of relative imports
try:
    from nodes.coordinator import CoordinatorNode
    from nodes.retriever import RetrieverNode
    from nodes.content_analyzer import ContentAnalyzerNode
    from nodes.context_processor import ContextProcessor
    from nodes.answer_synthesizer import AnswerSynthesizer
    from nodes.quality_validator import QualityValidatorNode
    from core.base_search import BaseSearchEngine
    from config.settings import SearchConfig
    from utils.state import SearchState
    NODES_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("⚠️ Some workflow components not available, using basic fallback")
    # Set these to None to prevent further errors
    CoordinatorNode = None
    RetrieverNode = None
    ContentAnalyzerNode = None
    ContextProcessor = None
    AnswerSynthesizer = None
    QualityValidatorNode = None
    BaseSearchEngine = None
    SearchConfig = None
    SearchState = None
    NODES_AVAILABLE = False

class MockNode:
    """Mock node for fallback functionality"""
    def __init__(self, name: str, search_engine=None):
        self.name = name
        self.search_engine = search_engine
        self.logger = logging.getLogger(__name__)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Mock process method"""
        self.logger.info(f"🔄 Processing {self.name} (fallback mode)")
        state["messages"].append(f"Processed {self.name} (fallback)")
        return state
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Allow calling as function"""
        return self.process(state)

class HybridSearchWorkflow:
    """Enhanced workflow orchestrator with better fallback handling"""
    
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        
        # Handle case where config might not be SearchConfig type
        if hasattr(config, 'opensearch_hosts'):
            self.config = config
        else:
            # Create a basic config if needed
            from dataclasses import dataclass
            @dataclass
            class BasicConfig:
                default_search_method: str = "hybrid"
                default_num_results: int = 5
                max_retries: int = 1
            self.config = BasicConfig()
        
        # Initialize search engine if possible
        if NODES_AVAILABLE and BaseSearchEngine:
            try:
                self.search_engine = BaseSearchEngine(self.config)
                self.logger.info("✅ Search engine initialized")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize search engine: {e}")
                self.search_engine = None
        else:
            self.search_engine = None
        
        # Initialize nodes with fallback
        self._init_nodes()
        
        # Build workflow if LangGraph is available
        if LANGGRAPH_AVAILABLE and StateGraph is not None and NODES_AVAILABLE:
            try:
                self.workflow = self._build_workflow()
                self.app = self.workflow.compile()
                self.logger.info("✅ LangGraph workflow compiled successfully")
            except Exception as e:
                self.logger.error(f"❌ Failed to build LangGraph workflow: {e}")
                self.workflow = None
                self.app = None
        else:
            self.workflow = None
            self.app = None
    
    def _init_nodes(self):
        """Initialize nodes with fallback to mock nodes"""
        try:
            if NODES_AVAILABLE and all([CoordinatorNode, RetrieverNode, ContentAnalyzerNode, 
                                      ContextProcessor, AnswerSynthesizer, QualityValidatorNode]):
                self.coordinator = CoordinatorNode(self.config)
                self.retriever = RetrieverNode(self.search_engine)
                self.content_analyzer = ContentAnalyzerNode()
                self.context_processor = ContextProcessor(self.config)
                self.answer_synthesizer = AnswerSynthesizer(self.search_engine)
                self.quality_validator = QualityValidatorNode(self.config)
                self.logger.info("✅ All workflow nodes initialized")
            else:
                raise ImportError("Workflow components not available")
        except Exception as e:
            self.logger.warning(f"⚠️ Using mock nodes due to: {e}")
            self.coordinator = MockNode("coordinator", self.search_engine)
            self.retriever = MockNode("retriever", self.search_engine)
            self.content_analyzer = MockNode("content_analyzer", self.search_engine)
            self.context_processor = MockNode("context_processor", self.search_engine)
            self.answer_synthesizer = MockNode("answer_synthesizer", self.search_engine)
            self.quality_validator = MockNode("quality_validator", self.search_engine)
    
    def _build_workflow(self):
        """Build the LangGraph workflow"""
        if not LANGGRAPH_AVAILABLE or StateGraph is None:
            return None
            
        try:
            workflow = StateGraph(SearchState if SearchState else Dict)
            
            # Add nodes with process methods
            workflow.add_node("coordinator", self.coordinator.process)
            workflow.add_node("retriever", self.retriever.process)
            workflow.add_node("content_analyzer", self.content_analyzer.process)
            workflow.add_node("context_processor", self.context_processor.process)
            workflow.add_node("answer_synthesizer", self.answer_synthesizer.process)
            workflow.add_node("quality_validator", self.quality_validator.process)
            
            # Set entry point
            workflow.set_entry_point("coordinator")
            
            # Define edges
            workflow.add_edge("coordinator", "retriever")
            workflow.add_edge("retriever", "content_analyzer")
            workflow.add_edge("content_analyzer", "context_processor")
            workflow.add_edge("context_processor", "answer_synthesizer")
            workflow.add_edge("answer_synthesizer", "quality_validator")
            
            # Fixed conditional edge with better logic
            workflow.add_conditional_edges(
                "quality_validator",
                self._should_retry_answer,
                {
                    "retry": "answer_synthesizer",
                    "accept": END
                }
            )
            
            return workflow
        except Exception as e:
            self.logger.error(f"❌ Error building workflow: {e}")
            return None
    
    def _should_retry_answer(self, state: Dict[str, Any]) -> str:
        """Decide whether to retry answer generation - fixed to prevent infinite loops"""
        validation_results = state.get("validation_results", {})
        retry_count = state.get("retry_count", 0)
        quality_score = validation_results.get("quality_score", 0.0)
        
        # More restrictive retry conditions
        should_retry = (
            validation_results.get("retry_recommended", False) and 
            retry_count < 1 and  # Maximum 1 retry
            quality_score < 0.3 and  # Only retry if quality is very low
            len(state.get("processed_context", "")) > 50  # Only retry if we have context
        )
        
        if should_retry:
            state["retry_count"] = retry_count + 1
            state["messages"].append(f"🔄 Retrying answer generation (attempt #{retry_count + 2})")
            return "retry"
        else:
            return "accept"
    
    def run(self, query: str, index_name: str, **kwargs) -> Dict[str, Any]:
        """Run the complete workflow with comprehensive error handling"""
        start_time = time.time()
        
        try:
            # Try LangGraph workflow first if available
            if LANGGRAPH_AVAILABLE and self.app:
                return self._run_langgraph_workflow(query, index_name, **kwargs)
            else:
                return self._run_fallback_workflow(query, index_name, **kwargs)
        except Exception as e:
            self.logger.error(f"❌ Workflow execution failed: {e}")
            return self._create_error_response(query, str(e), time.time() - start_time)
    
    def _run_langgraph_workflow(self, query: str, index_name: str, **kwargs) -> Dict[str, Any]:
        """Run workflow with LangGraph"""
        initial_state = {
            "query": query,
            "index_name": index_name,
            "search_method": kwargs.get("search_method", getattr(self.config, 'default_search_method', 'hybrid')),
            "num_results": kwargs.get("num_results", getattr(self.config, 'default_num_results', 5)),
            "messages": [],
            "step_times": {},
            "retry_count": 0,
            "current_step": "initialization",
            "error": None,
            "total_tokens": 0,
            "cost_estimate": 0.0,
            "search_results": [],
            "processed_context": "",
            "context_metadata": {},
            "content_analysis": {},
            "similarity_analysis": {},
            "answer_data": {},
            "validation_results": {},
            "quality_score": 0.0
        }
        
        try:
            result = self.app.invoke(initial_state)
            return self._format_result(result)
        except Exception as e:
            self.logger.error(f"❌ LangGraph workflow failed: {e}")
            return self._run_fallback_workflow(query, index_name, **kwargs)
        
    def _run_fallback_workflow(self, query: str, index_name: str, **kwargs) -> Dict[str, Any]:
        """Run workflow without LangGraph"""
        self.logger.info("🔄 Running fallback workflow...")
        
        # Initialize state
        state = {
            "query": query,
            "index_name": index_name,
            "search_method": kwargs.get("search_method", getattr(self.config, 'default_search_method', 'hybrid')),
            "num_results": kwargs.get("num_results", getattr(self.config, 'default_num_results', 5)),
            "messages": [],
            "current_step": "initialization",
            "error": None,
            "step_times": {},
            "total_tokens": 0,
            "cost_estimate": 0.0,
            "search_results": [],
            "processed_context": "",
            "context_metadata": {},
            "content_analysis": {},
            "similarity_analysis": {},
            "answer_data": {},
            "validation_results": {},
            "quality_score": 0.0,
            "retry_count": 0
        }
        
        # Run each node sequentially with error handling
        try:
            state = self._run_node_safely("coordinator", self.coordinator, state)
            state = self._run_node_safely("retriever", self.retriever, state)
            state = self._run_node_safely("content_analyzer", self.content_analyzer, state)
            state = self._run_node_safely("context_processor", self.context_processor, state)
            state = self._run_node_safely("answer_synthesizer", self.answer_synthesizer, state)
            state = self._run_node_safely("quality_validator", self.quality_validator, state)
        except Exception as e:
            self.logger.error(f"❌ Fallback workflow failed: {e}")
            state["error"] = str(e)
            state["answer_data"] = {"answer": f"Error processing query: {str(e)}"}
        
        return self._format_result(state)
    
    def _run_node_safely(self, node_name: str, node: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run a node with error handling"""
        start_time = time.time()
        try:
            state["current_step"] = node_name
            state = node(state)
            state["step_times"][node_name] = time.time() - start_time
            self.logger.info(f"✅ {node_name} completed in {state['step_times'][node_name]:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            state["step_times"][node_name] = elapsed
            state["messages"].append(f"❌ {node_name} failed: {str(e)}")
            self.logger.error(f"❌ {node_name} failed after {elapsed:.2f}s: {e}")
            
            # For critical nodes, add fallback behavior
            if node_name == "retriever":
                state["search_results"] = []
                state["messages"].append("Using empty search results as fallback")
            elif node_name == "answer_synthesizer":
                state["answer_data"] = {
                    "answer": "Unable to generate answer due to processing error.",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_estimate": 0.0
                }
        
        return state
    
    def _format_result(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Format the final result"""
        answer_data = state.get("answer_data", {})
        
        return {
            'query': state.get("query", ""),
            'search_results': state.get("search_results", []),
            'answer': answer_data.get("answer", "No answer generated"),
            'method': 'enhanced_hybrid_workflow',
            'num_results': len(state.get("search_results", [])),
            
            # Analysis results
            'content_analysis': state.get("content_analysis", {}),
            'similarity_analysis': state.get("similarity_analysis", {}),
            'validation_results': state.get("validation_results", {}),
            
            # Performance metrics
            'step_times': state.get("step_times", {}),
            'total_processing_time': sum(state.get("step_times", {}).values()),
            'input_tokens': answer_data.get("input_tokens", 0),
            'output_tokens': answer_data.get("output_tokens", 0),
            'total_tokens': answer_data.get("total_tokens", 0),
            'cost_estimate': answer_data.get("cost_estimate", 0.0),
            
            # Workflow tracking
            'workflow_messages': state.get("messages", []),
            'quality_score': state.get("quality_score", 0.0),
            'error': state.get("error"),
            'workflow_type': 'langgraph' if self.app else 'fallback'
        }
    
    def _create_error_response(self, query: str, error_message: str, processing_time: float) -> Dict[str, Any]:
        """Create error response"""
        return {
            'query': query,
            'search_results': [],
            'answer': f"Error processing query: {error_message}",
            'method': 'error_fallback',
            'num_results': 0,
            'content_analysis': {},
            'similarity_analysis': {},
            'validation_results': {},
            'step_times': {'error': processing_time},
            'total_processing_time': processing_time,
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'cost_estimate': 0.0,
            'workflow_messages': [f"❌ Critical error: {error_message}"],
            'quality_score': 0.0,
            'error': error_message,
            'workflow_type': 'error'
        }
    
    def health_check(self) -> Dict[str, bool]:
        """Check workflow health"""
        health = {
            'langgraph_available': LANGGRAPH_AVAILABLE,
            'nodes_available': NODES_AVAILABLE,
            'workflow_compiled': self.app is not None,
            'search_engine': False
        }
        
        if self.search_engine:
            try:
                engine_health = self.search_engine.health_check()
                health.update(engine_health)
                health['search_engine'] = any(engine_health.values())
            except Exception as e:
                self.logger.error(f"❌ Search engine health check failed: {e}")
        
        return health