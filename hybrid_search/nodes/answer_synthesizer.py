import time
import os
from typing import Dict, Any, Optional
from core.base_search import BaseSearchEngine
import google.generativeai as genai

class AnswerSynthesizer:
    """Enhanced answer synthesis with direct Gemini integration"""
    
    def __init__(self, search_engine: BaseSearchEngine, config=None):
        self.search_engine = search_engine
        self.config = config
        self.gemini_model = None
        self.answer_generator = None
        
        # Initialize Gemini directly (replacing DSPy integration)
        self._initialize_gemini()
        
        # Initialize our own reasoning system (replacing DSPy reasoning)
        self.answer_generator = AdvancedAnswerGenerator(self.gemini_model)
        
        if self.gemini_model:
            print("✅ Answer Generator initialized with direct Gemini integration")
        else:
            print("⚠️ Falling back to basic answer generation")
    
    def _initialize_gemini(self):
        """Initialize Gemini model directly (replacing the complex DSPy setup)"""
        try:
            # Get API key
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key or api_key == "mock_api_key_for_testing":
                print("⚠️ Using mock Gemini API key - real API calls will be simulated")
                self.gemini_model = None
                return
            
            # Configure and create model
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            
            print("✅ Gemini model initialized successfully")
                
        except Exception as e:
            print(f"⚠️ Failed to initialize Gemini: {e}")
            self.gemini_model = None
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process method for LangGraph compatibility"""
        return self.__call__(state)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive answer (keeping original structure)"""
        step_start = time.time()
        
        state["current_step"] = "answer_synthesis"
        
        # Ensure messages list exists
        if "messages" not in state:
            state["messages"] = []
        
        state["messages"].append("🧠 Answer Synthesizer: Generating comprehensive answer...")
        
        if not state.get("processed_context"):
            state["answer_data"] = self._empty_answer()
            state["step_times"] = state.get("step_times", {})
            state["step_times"]["answer_synthesis"] = time.time() - step_start
            return state
        
        try:
            # Generate reasoning using our enhanced system (replacing DSPy)
            reasoning = self._generate_reasoning(state)
            
            # Generate final answer with Gemini (keeping original approach)
            final_answer = self._generate_with_gemini(
                reasoning,
                state["processed_context"],
                state["query"]
            )
            
            state["answer_data"] = final_answer
            state["messages"].append(
                f"✅ Answer Synthesizer: Generated answer ({final_answer['output_tokens']} tokens)"
            )
            
        except Exception as e:
            state["error"] = f"Answer synthesis error: {str(e)}"
            state["answer_data"] = self._error_answer(e)
            state["messages"].append(f"❌ Answer Synthesizer: Error - {str(e)}")
        
        state["step_times"] = state.get("step_times", {})
        state["step_times"]["answer_synthesis"] = time.time() - step_start
        return state
    
    def _generate_reasoning(self, state: Dict[str, Any]) -> str:
        """Enhanced reasoning generation (replacing DSPy reasoning)"""
        
        # Try our enhanced reasoning if Gemini is available
        if self.answer_generator and self.gemini_model:
            try:
                state["messages"].append("🔮 Using enhanced reasoning with Gemini...")
                reasoning = self.answer_generator.generate_reasoning(
                    query=state["query"],
                    context=state["processed_context"],
                    content_analysis=state.get("content_analysis", {}),
                    similarity_analysis=state.get("similarity_analysis", {})
                )
                state["messages"].append("✅ Enhanced reasoning completed")
                return reasoning
                
            except Exception as reasoning_error:
                print(f"⚠️ Enhanced reasoning failed: {reasoning_error}. Using fallback.")
                state["messages"].append(f"⚠️ Enhanced reasoning failed, using fallback")
        
        # Fallback reasoning (keeping original logic but enhanced)
        state["messages"].append("🔧 Using fallback reasoning method")
        return self._generate_fallback_reasoning(
            state["query"],
            state["processed_context"],
            state.get("content_analysis", {}),
            state.get("similarity_analysis", {})
        )

    def _generate_with_gemini(self, reasoning: str, context, query: str) -> Dict[str, Any]:
        """Generate final answer with Gemini (keeping original structure, enhancing implementation)"""
        
        try:
            # Handle context conversion to string
            context_str = self._prepare_context_string(context)
            
            # Build enhanced prompt (improved version)
            enhanced_prompt = self._build_enhanced_prompt(reasoning, context_str, query)
            
            # Rate limiting (keeping original approach)
            if hasattr(self.search_engine, 'rate_limit_gemini'):
                self.search_engine.rate_limit_gemini()
            
            # Token counting (enhanced with fallback)
            input_tokens = self._count_tokens_safe(enhanced_prompt)
            
            # Generate content with Gemini (enhanced error handling)
            try:
                response = self.gemini_model.generate_content(
                    enhanced_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=1024,
                        top_p=0.8,
                        top_k=40,
                        candidate_count=1,
                    )
                )
                
                answer_text = self._extract_response_text(response)
                    
            except Exception as api_error:
                print(f"Gemini API error: {api_error}")
                # Fallback answer generation (keeping original approach)
                answer_text = self._generate_fallback_answer(reasoning, context_str, query)
            
            # Token counting for output
            output_tokens = self._count_tokens_safe(answer_text)
            
            return {
                'answer': answer_text,
                'input_tokens': int(input_tokens),
                'output_tokens': int(output_tokens),
                'total_tokens': int(input_tokens + output_tokens),
                'cost_estimate': self._estimate_cost(int(input_tokens), int(output_tokens))
            }
            
        except Exception as e:
            print(f"Error in _generate_with_gemini: {e}")
            return self._error_answer(e)
    
    def _prepare_context_string(self, context) -> str:
        """Enhanced context preparation (improved from original)"""
        if isinstance(context, dict):
            if 'content' in context:
                return str(context['content'])
            elif 'text' in context:
                return str(context['text'])
            elif 'results' in context:
                # Enhanced: Handle multiple search results with source attribution
                results = context['results']
                if isinstance(results, list):
                    context_parts = []
                    for i, result in enumerate(results[:10], 1):  # Limit to top 10
                        if isinstance(result, dict):
                            title = result.get('title', f'Source {i}')
                            content = result.get('content', result.get('snippet', ''))
                            url = result.get('url', '')
                            source_info = f"[Source {i}] {title}"
                            if url:
                                source_info += f" ({url})"
                            context_parts.append(f"{source_info}: {content}")
                        else:
                            context_parts.append(f"[Source {i}] {str(result)}")
                    return '\n\n'.join(context_parts)
            else:
                return str(context)
        elif isinstance(context, list):
            # Enhanced: Better list handling
            context_parts = []
            for i, item in enumerate(context[:10], 1):
                if isinstance(item, dict):
                    title = item.get('title', f'Item {i}')
                    content = item.get('content', item.get('snippet', str(item)))
                    context_parts.append(f"[Source {i}] {title}: {content}")
                else:
                    context_parts.append(f"[Source {i}] {str(item)}")
            return '\n\n'.join(context_parts)
        else:
            return str(context)
    
    def _build_enhanced_prompt(self, reasoning: str, context_str: str, query: str) -> str:
        """Enhanced prompt building (improved from original)"""
        return f"""You are an advanced AI research assistant with expert analytical capabilities.

ANALYTICAL REASONING:
{reasoning}

SEARCH CONTEXT:
{context_str}

RESEARCH QUESTION: {query}

INSTRUCTIONS:
- Synthesize a comprehensive, well-structured answer using the reasoning and context
- Reference specific sources using [Source X] format when citing information
- Organize complex information with clear sections or bullet points when appropriate
- Be precise and factual while maintaining readability
- If the context has limitations, acknowledge them transparently
- Integrate the analytical insights naturally into your response
- Aim for depth and accuracy over brevity

COMPREHENSIVE RESEARCH ANSWER:"""
    
    def _extract_response_text(self, response) -> str:
        """Enhanced response extraction (improved error handling)"""
        try:
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        return candidate.content.parts[0].text.strip()
            
            # Enhanced fallback handling
            response_str = str(response)
            if len(response_str) > 50:
                return response_str
            
            raise Exception("No valid response text found in Gemini response")
            
        except Exception as e:
            raise Exception(f"Failed to extract response text: {str(e)}")
    
    def _count_tokens_safe(self, text: str) -> int:
        """Enhanced token counting (improved from original)"""
        try:
            # Try using Gemini's native token counting
            if hasattr(self.gemini_model, 'count_tokens'):
                result = self.gemini_model.count_tokens(text)
                return result.total_tokens if hasattr(result, 'total_tokens') else result
        except Exception:
            pass
        
        # Enhanced fallback estimation
        word_count = len(text.split())
        # More accurate token estimation for Gemini
        return int(word_count * 1.3)

    def _generate_fallback_answer(self, reasoning: str, context: str, query: str) -> str:
        """Enhanced fallback answer generation (keeping original structure)"""
        
        answer_parts = []
        
        answer_parts.append(f"Based on the available research for: {query}")
        
        if reasoning and reasoning.strip():
            # Enhanced reasoning display
            clean_reasoning = reasoning.replace("|", " • ").strip()
            answer_parts.append(f"\nAnalytical Summary: {clean_reasoning}")
        
        # Enhanced context extraction
        if context and len(context) > 100:
            # Try to extract key sentences more intelligently
            sentences = [s.strip() for s in context.split('.') if s.strip() and len(s.strip()) > 20]
            if sentences:
                # Take first 3 substantial sentences
                key_info = '. '.join(sentences[:3])
                if not key_info.endswith('.'):
                    key_info += '.'
                answer_parts.append(f"\nKey Findings: {key_info}")
        
        answer_parts.append("\n\nNote: This response was generated using enhanced fallback processing. The analysis is based on available context but may have reduced detail due to API limitations.")
        
        return " ".join(answer_parts)
    
    def _generate_fallback_reasoning(self, query: str, context: str, 
                                   content_analysis: Dict, similarity_analysis: Dict) -> str:
        """Enhanced fallback reasoning (improved from original)"""
        reasoning_parts = []
        
        # Enhanced query analysis
        reasoning_parts.append(f"Research Query: '{query}' requires comprehensive analysis")
        
        # Enhanced content analysis insights
        if content_analysis:
            num_docs = content_analysis.get('num_documents', 0)
            if num_docs > 0:
                reasoning_parts.append(f"Processed {num_docs} source documents")
            
            top_keywords = content_analysis.get('top_keywords', [])[:5]
            if top_keywords:
                keywords = ", ".join([f"{kw[0]}({kw[1]:.2f})" for kw in top_keywords])
                reasoning_parts.append(f"Key concepts identified: {keywords}")
            
            avg_length = content_analysis.get('avg_doc_length', 0)
            if avg_length > 0:
                reasoning_parts.append(f"Average source length: {avg_length} words")
        
        # Enhanced similarity analysis insights
        if similarity_analysis:
            avg_sim = similarity_analysis.get('avg_similarity', 0)
            max_sim = similarity_analysis.get('max_similarity', 0)
            if avg_sim > 0:
                reasoning_parts.append(f"Content coherence: avg={avg_sim:.3f}, max={max_sim:.3f}")
        
        # Enhanced context analysis
        if isinstance(context, str):
            context_words = len(context.split())
            source_count = context.count('[Source') if '[Source' in context else 1
            reasoning_parts.append(f"Synthesizing {context_words} words from {source_count} sources")
        
        reasoning_parts.append("Applying comprehensive analytical framework for optimal response synthesis")
        
        return " | ".join(reasoning_parts)
    
    # Keep all the utility methods from original with same signatures
    def _empty_answer(self) -> Dict[str, Any]:
        return {
            'answer': "I couldn't find any relevant information to answer your question.",
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'cost_estimate': 0.0
        }
    
    def _error_answer(self, error: Exception) -> Dict[str, Any]:
        return {
            'answer': f"Error generating answer: {str(error)}",
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'cost_estimate': 0.0
        }
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for Gemini (keeping original logic)"""
        if input_tokens + output_tokens == 0:
            return 0.0
        input_cost = (input_tokens / 1_000_000) * 0.075
        output_cost = (output_tokens / 1_000_000) * 0.30
        return input_cost + output_cost


class AdvancedAnswerGenerator:
    """Direct Gemini-powered reasoning generator (replacing DSPy module)"""
    
    def __init__(self, gemini_model):
        self.gemini_model = gemini_model
    
    def generate_reasoning(self, query: str, context: str, content_analysis: Dict, similarity_analysis: Dict) -> str:
        """Generate analytical reasoning using Gemini directly"""
        
        # Prepare analysis summary
        analysis_summary = self._prepare_analysis_summary(content_analysis, similarity_analysis)
        
        # Manage context window intelligently
        managed_context = self._manage_context_window(context, max_tokens=4000)
        
        # Build reasoning prompt
        reasoning_prompt = f"""You are an expert research analyst. Analyze the following information and provide structured reasoning for answering the research question.

RESEARCH QUESTION: {query}

SEARCH CONTEXT:
{managed_context}

ANALYSIS DATA: {analysis_summary}

Please provide analytical reasoning that includes:
1. Key themes and patterns identified
2. Relevance assessment of available information
3. Information gaps or limitations
4. Synthesis approach for comprehensive answer

ANALYTICAL REASONING:"""
        
        try:
            response = self.gemini_model.generate_content(
                reasoning_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Lower temperature for more analytical reasoning
                    max_output_tokens=512,
                    top_p=0.9,
                    top_k=40,
                )
            )
            
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            else:
                raise Exception("No reasoning generated")
                
        except Exception as e:
            print(f"Reasoning generation failed: {e}")
            # Enhanced fallback reasoning
            return self._generate_enhanced_fallback_reasoning(query, managed_context, analysis_summary)
    
    def _manage_context_window(self, context: str, max_tokens: int = 4000) -> str:
        """Intelligent context window management"""
        
        # Rough token estimation
        estimated_tokens = len(context.split()) * 1.3
        
        if estimated_tokens <= max_tokens:
            return context
        
        # Smart truncation by sources
        if '[Source' in context:
            sources = context.split('\n\n')
            result_parts = []
            current_tokens = 0
            
            for part in sources:
                part_tokens = len(part.split()) * 1.3
                if current_tokens + part_tokens > max_tokens:
                    break
                result_parts.append(part)
                current_tokens += part_tokens
            
            result = '\n\n'.join(result_parts)
            if len(result_parts) < len(sources):
                result += f"\n\n[Context truncated - showing {len(result_parts)} of {len(sources)} sources]"
            return result
        
        # Simple word-based truncation
        words = context.split()
        max_words = int(max_tokens * 0.75)
        if len(words) > max_words:
            truncated = ' '.join(words[:max_words])
            return truncated + '\n\n[Content truncated for length management]'
        
        return context
    
    def _prepare_analysis_summary(self, content_analysis: Dict, similarity_analysis: Dict) -> str:
        """Enhanced analysis summary preparation"""
        summary_parts = []
        
        if content_analysis:
            num_docs = content_analysis.get('num_documents', 0)
            if num_docs > 0:
                summary_parts.append(f"Documents: {num_docs}")
            
            top_keywords = content_analysis.get('top_keywords', [])[:3]
            if top_keywords:
                keywords = ", ".join([f"{kw[0]}({kw[1]:.2f})" for kw in top_keywords])
                summary_parts.append(f"Key themes: {keywords}")
            
            avg_length = content_analysis.get('avg_doc_length', 0)
            if avg_length > 0:
                summary_parts.append(f"Avg length: {avg_length}w")
        
        if similarity_analysis:
            avg_sim = similarity_analysis.get('avg_similarity', 0)
            if avg_sim > 0:
                summary_parts.append(f"Similarity: {avg_sim:.3f}")
        
        return " | ".join(summary_parts) if summary_parts else "Basic content analysis"
    
    def _generate_enhanced_fallback_reasoning(self, query: str, context: str, analysis: str) -> str:
        """Enhanced fallback reasoning when Gemini fails"""
        
        reasoning_parts = []
        
        # Query analysis
        reasoning_parts.append(f"Analytical approach for: '{query}'")
        
        # Context assessment
        if context:
            word_count = len(context.split())
            source_count = context.count('[Source') if '[Source' in context else 1
            reasoning_parts.append(f"Processing {word_count} words from {source_count} sources")
        
        # Analysis integration
        if analysis and analysis.strip():
            reasoning_parts.append(f"Data insights: {analysis}")
        
        # Synthesis approach
        reasoning_parts.append("Applying structured synthesis methodology")
        reasoning_parts.append("Prioritizing factual accuracy and comprehensive coverage")
        
        return " | ".join(reasoning_parts)