import time
import numpy as np
from typing import Dict, Any
from config.settings import SearchConfig
from utils.serialization import convert_numpy_values

class QualityValidatorNode:
    """Quality validator agent - validates answer quality"""
    
    def __init__(self, config: SearchConfig):
        self.config = config
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process method for LangGraph compatibility"""
        return self(state)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate answer quality"""
        step_start = time.time()
        
        state["current_step"] = "quality_validation"
        state["messages"].append("✅ Quality Validator: Assessing answer quality...")
        
        answer_data = state.get("answer_data", {})
        answer = answer_data.get("answer", "")
        
        if not answer or len(answer) < 10:
            state["validation_results"] = {
                'quality_score': 0.0,
                'issues': ['Answer too short or empty'],
                'validation_passed': False,
                'retry_recommended': True
            }
            state["quality_score"] = 0.0
            state["step_times"]["quality_validation"] = time.time() - step_start
            return state
        
        try:
            issues = []
            quality_factors = []
            
            # Length check
            if len(answer) < 100:
                issues.append("Answer might be too brief")
                quality_factors.append(0.4)
            elif len(answer) > 2000:
                issues.append("Answer might be too verbose")
                quality_factors.append(0.7)
            else:
                quality_factors.append(0.9)
            
            # Source reference check
            source_references = sum(1 for i in range(1, 6) if f"Source {i}" in answer or f"[{i}]" in answer)
            if source_references > 0:
                quality_factors.append(0.9)
            else:
                issues.append("Answer doesn't reference sources adequately")
                quality_factors.append(0.5)
            
            # Content relevance check
            query_words = set(state["query"].lower().split())
            answer_words = set(answer.lower().split())
            relevance_ratio = len(query_words & answer_words) / len(query_words) if query_words else 0
            
            if relevance_ratio > 0.5:
                quality_factors.append(0.9)
            elif relevance_ratio > 0.3:
                quality_factors.append(0.7)
            else:
                issues.append("Answer may not be fully relevant to query")
                quality_factors.append(0.4)
            
            # Analysis integration check
            if state.get("content_analysis") and any(kw[0] in answer.lower() for kw in state["content_analysis"].get("top_keywords", [])[:3]):
                quality_factors.append(0.8)  # Good integration of analysis
            else:
                quality_factors.append(0.6)  # Moderate integration
            
            # Calculate overall quality score
            quality_score = np.mean(quality_factors) if quality_factors else 0.0
            validation_passed = quality_score > self.config.quality_threshold and len(issues) <= 1
            retry_recommended = quality_score < self.config.retry_threshold
            
            validation_results = {
                'quality_score': float(quality_score),
                'issues': issues,
                'validation_passed': bool(validation_passed),
                'retry_recommended': bool(retry_recommended),
                'source_references': source_references,
                'relevance_ratio': float(relevance_ratio),
                'quality_factors': [float(factor) for factor in quality_factors]
            }
            
            # Ensure all values are serializable
            state["validation_results"] = convert_numpy_values(validation_results)
            state["quality_score"] = float(quality_score)
            
            if validation_passed:
                state["messages"].append(f"✅ Quality Validator: Answer approved (score: {quality_score:.2f})")
            else:
                state["messages"].append(f"⚠️ Quality Validator: Quality concerns (score: {quality_score:.2f})")
                if issues:
                    state["messages"].append(f"   Issues: {', '.join(issues)}")
            
        except Exception as e:
            state["error"] = f"Quality validation error: {str(e)}"
            state["validation_results"] = {
                'quality_score': 0.5,
                'issues': [f"Validation error: {str(e)}"],
                'validation_passed': False,
                'retry_recommended': False
            }
            state["quality_score"] = 0.5
            state["messages"].append(f"❌ Quality Validator: Error - {str(e)}")
        
        state["step_times"]["quality_validation"] = time.time() - step_start
        return state 