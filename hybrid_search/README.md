# Hybrid Search System with LangGraph, DSPy, and LlamaIndex

A modular, enterprise-grade hybrid search system that combines vector search, BM25, and multi-stage hybrid search with advanced context processing and answer synthesis using LangGraph, DSPy, and LlamaIndex.

## 🚀 Features

- **Multi-Method Search**: Vector search, BM25, and hybrid multi-stage search
- **LangGraph Workflow**: Orchestrated multi-agent workflow with state management
- **DSPy Integration**: Intelligent context optimization and answer reasoning
- **LlamaIndex Integration**: Advanced context window management
- **Quality Validation**: Automated answer quality assessment and retry logic
- **Performance Tracking**: Comprehensive metrics and cost estimation
- **Modular Architecture**: Easy to extend and customize

## 📁 Project Structure

```
hybrid_search/
├── __init__.py
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration management
├── core/
│   ├── __init__.py
│   └── base_search.py       # Base search engine
├── nodes/
│   ├── __init__.py
│   ├── coordinator.py       # Workflow coordination
│   ├── retriever.py        # Search execution
│   ├── content_analyzer.py # Content analysis
│   ├── context_processor.py # DSPy/LlamaIndex context processing
│   ├── answer_synthesizer.py # Answer generation
│   └── quality_validator.py # Quality validation
├── workflows/
│   ├── __init__.py
│   └── langgraph_workflow.py # LangGraph workflow orchestrator
├── utils/
│   ├── __init__.py
│   ├── state.py            # State definitions
│   ├── token_counter.py    # Token counting utilities
│   └── serialization.py    # Data serialization
└── main.py                 # Main entry point
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- OpenSearch instance running
- Gemini API key

### Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Or install optional dependencies separately
pip install opensearch-py sentence-transformers google-generativeai tiktoken numpy
pip install langgraph langchain-core dspy-ai llama-index
```

### Environment Setup

```bash
# Set your Gemini API key
export GEMINI_API_KEY='your-api-key-here'

# Or set it in your Python environment
import os
os.environ['GEMINI_API_KEY'] = 'your-api-key-here'
```

## 🎯 Quick Start

### Basic Usage

```python
from hybrid_search.config.settings import SearchConfig
from hybrid_search.workflows.langgraph_workflow import HybridSearchWorkflow

# Initialize configuration
config = SearchConfig(
    max_context_tokens=8000,
    max_output_tokens=1024,
    default_search_method="multi_stage"
)

# Create workflow
workflow = HybridSearchWorkflow(config)

# Run a search
result = workflow.run(
    index_name="passage_index",
    query="What is the importance of communication in science?",
    search_method="auto",
    num_results=5
)

print(f"Answer: {result['answer']}")
```

### Interactive Session

```bash
python main.py
```

This will start an interactive session where you can:
- Ask questions
- Change search methods
- Adjust result counts
- Toggle workflow visibility

## 🔧 Configuration

### SearchConfig Options

```python
from hybrid_search.config.settings import SearchConfig

config = SearchConfig(
    # OpenSearch settings
    opensearch_hosts=[{'host': 'localhost', 'port': 9200}],
    opensearch_timeout=30,
    opensearch_max_retries=10,
    
    # Model settings
    embedding_model='all-MiniLM-L6-v2',
    gemini_api_key='your-key-here',
    
    # Search settings
    default_search_method="multi_stage",
    default_num_results=5,
    search_size=500,
    
    # Context window settings
    max_context_tokens=8000,
    max_output_tokens=1024,
    context_overlap=200,
    
    # Quality thresholds
    quality_threshold=0.7,
    retry_threshold=0.5,
    max_retries=1
)
```

## 🔄 Workflow Architecture

The system uses a multi-agent workflow with the following nodes:

1. **Coordinator**: Analyzes queries and plans search strategy
2. **Retriever**: Executes multi-method search
3. **Content Analyzer**: Analyzes document content patterns
4. **Context Processor**: Optimizes context using DSPy/LlamaIndex
5. **Answer Synthesizer**: Generates comprehensive answers
6. **Quality Validator**: Assesses answer quality and triggers retries

### Workflow Flow

```
Query → Coordinator → Retriever → Content Analyzer → Context Processor → Answer Synthesizer → Quality Validator → Result
                                                                                    ↓
                                                                              Retry if needed
```

## 🧠 Advanced Features

### DSPy Integration

The system uses DSPy for intelligent context optimization and answer reasoning:

```python
# Context optimization with DSPy
context_optimizer = ContextOptimizer()
optimized_context = context_optimizer(
    query=query,
    documents=documents,
    max_tokens=8000
)

# Answer generation with DSPy
answer_generator = AdvancedAnswerGenerator()
reasoning = answer_generator(
    query=query,
    context=context,
    content_analysis=analysis,
    similarity_analysis=similarity
)
```

### LlamaIndex Integration

Advanced context window management with LlamaIndex:

```python
# Document processing
documents = [Document(text=text, metadata=metadata) for text, metadata in docs]

# Create index and query engine
index = VectorStoreIndex.from_documents(documents)
query_engine = RetrieverQueryEngine(
    retriever=index.as_retriever(similarity_top_k=5),
    response_synthesizer=get_response_synthesizer(response_mode="tree_summarize")
)
```

### Quality Validation

Automated quality assessment with configurable thresholds:

```python
# Quality factors assessed:
# - Answer length
# - Source references
# - Content relevance
# - Analysis integration

validation_results = {
    'quality_score': 0.85,
    'validation_passed': True,
    'retry_recommended': False,
    'source_references': 3,
    'relevance_ratio': 0.7
}
```

## 📊 Performance Metrics

The system tracks comprehensive performance metrics:

```python
result = {
    'step_times': {
        'coordination': 0.02,
        'retrieval': 0.15,
        'content_analysis': 0.08,
        'context_processing': 0.12,
        'answer_synthesis': 2.34,
        'quality_validation': 0.03
    },
    'total_processing_time': 2.74,
    'input_tokens': 1250,
    'output_tokens': 450,
    'total_tokens': 1700,
    'cost_estimate': 0.000127,
    'quality_score': 0.85
}
```

## 🔧 Customization

### Adding New Search Methods

```python
class CustomSearchNode:
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Your custom search logic here
        pass

# Add to workflow
workflow.add_node("custom_search", CustomSearchNode())
```

### Custom Quality Validators

```python
class CustomQualityValidator:
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Your custom quality assessment logic
        pass
```

### Extending Context Processing

```python
class CustomContextProcessor:
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Your custom context processing logic
        pass
```

## Database & Migrations

This project uses PostgreSQL with SQLAlchemy models and Alembic migrations (Redis is used for session caching).

- Set `DATABASE_URL` (e.g., `postgresql://postgres:your_postgres_password@localhost:5432/hybrid_search`).
- On server startup, migrations are applied automatically; existing hand-created tables are stamped to the baseline if needed.
- To run migrations manually:

```bash
alembic upgrade head
```

Chat data persistence: `/search` accepts optional `chat_session_id`. If omitted, a new session is created and both user query and assistant answer are stored in `chat_messages` under that session.

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=hybrid_search tests/
```

## 📈 Monitoring

The system provides comprehensive monitoring capabilities:

- **Performance Metrics**: Step-by-step timing
- **Token Usage**: Input/output token tracking
- **Cost Estimation**: API cost tracking
- **Quality Scores**: Answer quality assessment
- **Error Tracking**: Comprehensive error handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **LangGraph**: For workflow orchestration
- **DSPy**: For intelligent context optimization
- **LlamaIndex**: For advanced context management
- **OpenSearch**: For search capabilities
- **Google Gemini**: For answer generation

## 📞 Support

For questions and support:
- Open an issue on GitHub
- Check the documentation
- Review the examples

---

**Happy Searching! 🔍✨**