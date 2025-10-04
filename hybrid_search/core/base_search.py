from opensearchpy import OpenSearch
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from typing import List, Dict, Any, Optional, Tuple
import time
import tiktoken
import numpy as np
import logging
import requests
from contextlib import asynccontextmanager
import asyncio

from config.settings import SearchConfig

class BaseSearchEngine:
    """Enhanced base class for search functionality with HNSW support and connection handling"""
    
    def __init__(self, config: SearchConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Wait for services to be ready
        if not config.wait_for_services():
            self.logger.warning("⚠️ Services may not be fully ready")
        # Initialize OpenSearch with better configuration and retry logic
        self._init_opensearch()
        
        # Initialize embedding model with error handling
        self._init_embedding_model()
        
        # Initialize Gemini with better error handling
        self._init_gemini()
        
        # Rate limiting and performance tracking
        self.last_request_time = 0
        self.request_count = 0
        self.total_tokens_used = 0
        
        # Token counter
        self._init_tokenizer()

    def _init_opensearch(self):
        """Initialize OpenSearch with connection retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Ensure timeout is numeric
                timeout = self.config.opensearch_timeout
                if isinstance(timeout, str):
                    timeout = int(timeout.replace('s', ''))
                self.client = OpenSearch(
                    hosts=self.config.opensearch_hosts,
                    timeout=timeout,
                    max_retries=self.config.opensearch_max_retries,
                    retry_on_timeout=True,
                    verify_certs=self.config.opensearch_verify_certs,
                    ssl_assert_hostname=False,
                    ssl_show_warn=False,
                    use_ssl=self.config.opensearch_use_ssl,
                    # Add connection-specific timeout settings
                    connection_class=None,
                    http_compress=True,
                )
                
                # Test the connection with proper timeout
                cluster_health = self.client.cluster.health(timeout=timeout)
                self.logger.info(f"✅ OpenSearch connected successfully: {cluster_health['status']}")
                return
                
            except Exception as e:
                self.logger.warning(f"⚠️ OpenSearch connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error("❌ Failed to connect to OpenSearch after all retries")
                    raise ConnectionError(f"Could not connect to OpenSearch: {e}")

    def _init_embedding_model(self):
        """Initialize embedding model with error handling"""
        try:
            self.model = SentenceTransformer(self.config.embedding_model)
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            self.logger.info(f"✅ Embedding model loaded: {self.config.embedding_model} (dim: {self.embedding_dimension})")
        except Exception as e:
            self.logger.error(f"❌ Failed to load embedding model: {e}")
            raise

    def _init_gemini(self):
        """Initialize Gemini with proper error handling"""
        if not self.config.gemini_api_key or self.config.gemini_api_key == "mock_api_key_for_testing":
            self.logger.warning("⚠️ Using mock Gemini API key - real API calls will be simulated")
            self.gemini_model = None
            return
            
        try:
            genai.configure(api_key=self.config.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Test the connection - but don't fail if it doesn't work
            try:
                test_response = self.gemini_model.generate_content("Hello")
                if test_response and test_response.text:
                    self.logger.info("✅ Gemini model initialized and tested successfully")
                else:
                    self.logger.warning("⚠️ Gemini model initialized but test failed")
            except Exception as test_e:
                self.logger.warning(f"⚠️ Gemini model initialized but test failed: {test_e}")
                
        except Exception as e:
            self.logger.error(f"⚠️ Failed to initialize Gemini: {e}")
            self.gemini_model = None

    def _init_tokenizer(self):
        """Initialize token counter"""
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            self.logger.warning(f"Failed to load tokenizer: {e}")
            self.tokenizer = None

    def ensure_connection(self):
        """Ensure OpenSearch connection is healthy"""
        try:
            # Use numeric timeout
            timeout = self.config.opensearch_timeout
            if isinstance(timeout, str):
                timeout = int(timeout.replace('s', ''))
            
            self.client.cluster.health(timeout=f"{timeout}s")
            return True
        except Exception as e:
            self.logger.warning(f"OpenSearch connection lost, attempting to reconnect: {e}")
            try:
                self._init_opensearch()
                return True
            except Exception as reconnect_e:
                self.logger.error(f"Failed to reconnect to OpenSearch: {reconnect_e}")
                return False

    def create_hnsw_index(self, index_name: str, dimension: Optional[int] = None, 
                         m: int = 16, ef_construction: int = 200) -> bool:
        """Create an index with optimized HNSW configuration"""
        
        if not self.ensure_connection():
            return False
            
        if dimension is None:
            dimension = self.embedding_dimension
            
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100,
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "refresh_interval": "30",
                    "max_result_window": 10000
                },
                "analysis": {
                    "analyzer": {
                        "custom_text_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop", "stemmer"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "passage_text": {
                        "type": "text",
                        "analyzer": "custom_text_analyzer",
                        "search_analyzer": "custom_text_analyzer"
                    },
                    "passage_embedding": {
                        "type": "knn_vector",
                        "dimension": dimension,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": ef_construction,
                                "m": m
                            }
                        }
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "keyword"},
                            "timestamp": {"type": "date"},
                            "chunk_id": {"type": "keyword"},
                            "document_id": {"type": "keyword"}
                        }
                    }
                }
            }
        }
        
        try:
            if self.client.indices.exists(index=index_name):
                self.logger.info(f"✅ Index {index_name} already exists")
                return True
                
            response = self.client.indices.create(index=index_name, body=index_body)
            self.logger.info(f"✅ Created HNSW index {index_name}")
            
            # Wait for index to be ready with proper timeout
            timeout = self.config.opensearch_timeout
            if isinstance(timeout, str):
                timeout = int(timeout.replace('s', ''))
            self.client.cluster.health(index=index_name, wait_for_status='yellow', timeout=f"{timeout}s")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error creating HNSW index: {e}")
            return False

    def vector_search(self, index_name: str, query_text: str, size: int = 500, 
                     ef_search: Optional[int] = None) -> List[Dict]:
        """Perform HNSW-accelerated vector search"""
        if not self.ensure_connection():
            return []
            
        try:
            query_vector = self.model.encode(query_text).tolist()
            
            # Configure HNSW search parameters
            knn_query = {
                "vector": query_vector,
                "k": size
            }
            
            if ef_search:
                knn_query["method_parameters"] = {"ef": ef_search}
            
            search_body = {
                "size": size,
                "query": {
                    "knn": {
                        "passage_embedding": knn_query
                    }
                },
                "_source": ["passage_text", "metadata"]
            }
            
            response = self.client.search(index=index_name, body=search_body)
            return response['hits']['hits']
            
        except Exception as e:
            self.logger.error(f"❌ Error in HNSW vector search: {e}")
            return []

    def hybrid_search(self, index_name: str, query_text: str, size: int = 500,
                     vector_weight: float = 0.7, text_weight: float = 0.3,
                     ef_search: Optional[int] = None) -> List[Dict]:
        """Perform hybrid search combining HNSW vector search and BM25"""
        if not self.ensure_connection():
            return []
            
        try:
            query_vector = self.model.encode(query_text).tolist()
            
            # Configure HNSW parameters
            knn_params = {"vector": query_vector, "k": size}
            if ef_search:
                knn_params["method_parameters"] = {"ef": ef_search}
            
            # Try hybrid query first
            hybrid_query = {
                "size": size,
                "query": {
                    "hybrid": {
                        "queries": [
                            {
                                "knn": {
                                    "passage_embedding": knn_params
                                }
                            },
                            {
                                "match": {
                                    "passage_text": {
                                        "query": query_text,
                                        "operator": "or"
                                    }
                                }
                            }
                        ],
                        "combination": {
                            "technique": "arithmetic_mean",
                            "weights": [vector_weight, text_weight]
                        }
                    }
                },
                "_source": ["passage_text", "metadata"]
            }
            
            try:
                response = self.client.search(index=index_name, body=hybrid_query)
                return response['hits']['hits']
            except Exception as hybrid_e:
                self.logger.warning(f"Hybrid search failed, falling back to separate searches: {hybrid_e}")
                return self._fallback_hybrid_search(index_name, query_text, size, 
                                                  vector_weight, text_weight, ef_search)
                
        except Exception as e:
            self.logger.error(f"❌ Error in hybrid search: {e}")
            return []

    def _fallback_hybrid_search(self, index_name: str, query_text: str, size: int,
                               vector_weight: float, text_weight: float,
                               ef_search: Optional[int]) -> List[Dict]:
        """Fallback hybrid search using separate queries"""
        try:
            vector_results = self.vector_search(index_name, query_text, size, ef_search)
            bm25_results = self.bm25_search(index_name, query_text, size)
            
            # Combine and rerank results
            combined_scores = {}
            
            # Add vector search scores
            for i, hit in enumerate(vector_results):
                doc_id = hit['_id']
                vector_score = hit['_score'] * vector_weight
                combined_scores[doc_id] = {
                    'score': vector_score,
                    'doc': hit,
                    'vector_rank': i + 1
                }
            
            # Add BM25 scores
            for i, hit in enumerate(bm25_results):
                doc_id = hit['_id']
                bm25_score = hit['_score'] * text_weight
                
                if doc_id in combined_scores:
                    combined_scores[doc_id]['score'] += bm25_score
                    combined_scores[doc_id]['bm25_rank'] = i + 1
                else:
                    combined_scores[doc_id] = {
                        'score': bm25_score,
                        'doc': hit,
                        'bm25_rank': i + 1
                    }
            
            # Sort by combined score and return
            sorted_results = sorted(combined_scores.values(), 
                                  key=lambda x: x['score'], reverse=True)
            
            return [result['doc'] for result in sorted_results[:size]]
            
        except Exception as e:
            self.logger.error(f"❌ Error in fallback hybrid search: {e}")
            return []

    def bm25_search(self, index_name: str, query_text: str, size: int = 500) -> List[Dict]:
        """Perform BM25 text search"""
        if not self.ensure_connection():
            return []
            
        try:
            bm25_query = {
                "size": size,
                "query": {
                    "match": {
                        "passage_text": {
                            "query": query_text,
                            "operator": "or"
                        }
                    }
                },
                "_source": ["passage_text", "metadata"]
            }
            
            response = self.client.search(index=index_name, body=bm25_query)
            return response['hits']['hits']
            
        except Exception as e:
            self.logger.error(f"❌ Error in BM25 search: {e}")
            return []

    async def bulk_index_documents(self, index_name: str, documents: List[Dict], 
                                  batch_size: int = 100) -> bool:
        """Bulk index documents with embeddings"""
        if not self.ensure_connection():
            return False
            
        from opensearchpy.helpers import bulk
        
        def generate_docs():
            for i, doc in enumerate(documents):
                # Generate embedding if not provided
                if 'passage_embedding' not in doc:
                    doc['passage_embedding'] = self.model.encode(doc['passage_text']).tolist()
                
                yield {
                    '_index': index_name,
                    '_id': doc.get('id', i),
                    '_source': doc
                }
        
        try:
            success, failed = bulk(
                self.client,
                generate_docs(),
                chunk_size=batch_size,
                request_timeout=60
            )
            
            self.logger.info(f"✅ Successfully indexed {success} documents, {len(failed)} failed")
            
            # Refresh index
            self.client.indices.refresh(index=index_name)
            return len(failed) == 0
            
        except Exception as e:
            self.logger.error(f"❌ Error bulk indexing: {e}")
            return False

    def vector_search_with_filters(self, index_name: str, query_text: str, 
                                  filters: Optional[Dict] = None, size: int = 500, 
                                  ef_search: Optional[int] = None) -> List[Dict]:
        """Perform filtered HNSW vector search"""
        if not self.ensure_connection():
            return []
            
        try:
            query_vector = self.model.encode(query_text).tolist()
            
            knn_query = {
                "vector": query_vector,
                "k": size
            }
            
            if ef_search:
                knn_query["method_parameters"] = {"ef": ef_search}
            
            # Add filters if provided
            query_body = {
                "size": size,
                "query": {
                    "knn": {
                        "passage_embedding": knn_query
                    }
                },
                "_source": ["passage_text", "metadata"]
            }
            
            if filters:
                query_body["query"] = {
                    "bool": {
                        "must": [
                            {"knn": {"passage_embedding": knn_query}}
                        ],
                        "filter": self._build_filter_query(filters)
                    }
                }
            
            response = self.client.search(index=index_name, body=query_body)
            return response['hits']['hits']
            
        except Exception as e:
            self.logger.error(f"❌ Error in filtered vector search: {e}")
            return []

    def _build_filter_query(self, filters: Dict) -> List[Dict]:
        """Build filter query from filters dictionary"""
        filter_queries = []
        
        for field, value in filters.items():
            if isinstance(value, list):
                filter_queries.append({"terms": {field: value}})
            elif isinstance(value, dict):
                if 'range' in value:
                    filter_queries.append({"range": {field: value['range']}})
            else:
                filter_queries.append({"term": {field: value}})
        
        return filter_queries

    def optimize_hnsw_parameters(self, index_name: str, sample_queries: List[str],
                                ground_truth: List[List[str]], 
                                ef_search_values: List[int] = [50, 100, 200, 400]) -> Dict:
        """Find optimal HNSW parameters for given queries"""
        if not self.ensure_connection():
            return {"ef_search": 100, "recall": 0.0, "latency": float('inf')}
            
        best_params = {"ef_search": 100, "recall": 0.0, "latency": float('inf')}
        
        for ef_search in ef_search_values:
            total_recall = 0.0
            total_latency = 0.0
            
            for i, query in enumerate(sample_queries):
                start_time = time.time()
                results = self.vector_search(index_name, query, size=10, ef_search=ef_search)
                latency = time.time() - start_time
                
                # Calculate recall
                retrieved_ids = [hit['_id'] for hit in results]
                true_ids = ground_truth[i] if i < len(ground_truth) else []
                recall = len(set(retrieved_ids) & set(true_ids)) / max(len(true_ids), 1)
                
                total_recall += recall
                total_latency += latency
            
            avg_recall = total_recall / len(sample_queries)
            avg_latency = total_latency / len(sample_queries)
            
            self.logger.info(f"ef_search={ef_search}: recall={avg_recall:.3f}, latency={avg_latency:.3f}ms")
            
            # Update best parameters (prioritize recall, then latency)
            if avg_recall > best_params["recall"] or \
               (avg_recall == best_params["recall"] and avg_latency < best_params["latency"]):
                best_params = {
                    "ef_search": ef_search,
                    "recall": avg_recall,
                    "latency": avg_latency
                }
        
        return best_params

    def get_index_stats(self, index_name: str) -> Dict:
        """Get HNSW index statistics"""
        if not self.ensure_connection():
            return {}
            
        try:
            stats = self.client.indices.stats(index=index_name)
            index_stats = stats['indices'][index_name]
            
            return {
                "document_count": index_stats['total']['docs']['count'],
                "store_size": index_stats['total']['store']['size_in_bytes'],
                "segments": index_stats['total']['segments']['count'],
                "memory_usage": index_stats['total']['segments']['memory_in_bytes']
            }
        except Exception as e:
            self.logger.error(f"❌ Error getting index stats: {e}")
            return {}

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            return len(text) // 4

    def rate_limit_gemini(self):
        """Apply rate limiting for Gemini"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.config.min_request_interval:
            sleep_time = self.config.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def estimate_cost(self, input_tokens: int, output_tokens: int = 0) -> float:
        """Estimate cost for Gemini"""
        if input_tokens + output_tokens == 0:
            return 0.0
        input_cost = (input_tokens / 1_000_000) * 0.075
        output_cost = (output_tokens / 1_000_000) * 0.30
        return input_cost + output_cost

    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        return {
            "total_requests": self.request_count,
            "total_tokens_used": self.total_tokens_used,
            "avg_tokens_per_request": self.total_tokens_used / max(self.request_count, 1),
            "estimated_total_cost": self.estimate_cost(self.total_tokens_used, 0)
        }

    def health_check(self) -> Dict[str, bool]:
        """Check health of all components"""
        health = {}
        
        # OpenSearch health
        try:
            cluster_health = self.client.cluster.health(timeout='5')
            health['opensearch'] = cluster_health['status'] in ['green', 'yellow']
        except Exception:
            health['opensearch'] = False
        
        # Embedding model health
        try:
            test_embedding = self.model.encode("test")
            health['embedding_model'] = len(test_embedding) > 0
        except Exception:
            health['embedding_model'] = False
        
        # Gemini health
        if self.gemini_model:
            try:
                test_response = self.gemini_model.generate_content("test")
                health['gemini'] = bool(test_response and test_response.text)
            except Exception:
                health['gemini'] = False
        else:
            health['gemini'] = False
        
        return health