from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import os
import logging

@dataclass
class SearchConfig:
    """Enhanced configuration for the hybrid search system"""

    # OpenSearch settings
    opensearch_hosts: List[Dict[str, Any]] = None
    opensearch_timeout: int = 30
    opensearch_max_retries: int = 10
    opensearch_use_ssl: bool = False
    opensearch_verify_certs: bool = False

    # Model settings
    embedding_model: str = 'all-MiniLM-L6-v2'
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", "mock_api_key_for_testing")

    # Search settings
    default_search_method: str = "multi_stage"
    default_num_results: int = 5
    search_size: int = 500

    # Context window settings
    max_context_tokens: int = 8000
    max_output_tokens: int = 1024
    context_overlap: int = 200

    # Rate limiting
    min_request_interval: float = 1.0

    # Quality thresholds
    quality_threshold: float = 0.7
    retry_threshold: float = 0.5
    max_retries: int = 1

    # Logging
    log_level: str = "INFO"
    
    # Feature flags
    enable_dspy: bool = False
    enable_llamaindex: bool = False
    
    def __post_init__(self):
        """Initialize configuration after creation"""
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configure OpenSearch hosts from environment variables
        if self.opensearch_hosts is None:
            host = os.getenv('OPENSEARCH_HOST', 'opensearch')
            port = int(os.getenv('OPENSEARCH_PORT', '9200'))
            scheme = os.getenv('OPENSEARCH_SCHEME', 'http')
            
            self.opensearch_hosts = [{
                'host': host,
                'port': port,
                'use_ssl': scheme == 'https'
            }]
            
            # Update SSL settings based on scheme
            self.opensearch_use_ssl = scheme == 'https'
            
        print(f"🔍 OpenSearch configured: {self.opensearch_hosts}")

        # Get Gemini API key from environment
        if self.gemini_api_key is None:
            self.gemini_api_key = (
                os.getenv('GEMINI_API_KEY') or
                os.getenv('GOOGLE_API_KEY') or
                os.getenv('GOOGLE_GEMINI_API_KEY')
            )

        # Validate and clean up API key
        if self.gemini_api_key:
            self.gemini_api_key = self.gemini_api_key.strip()
            if self.gemini_api_key in ['mock_api_key_for_testing', 'your_api_key_here', 'your_actual_gemini_api_key_here', '']:
                print("⚠️ Please set a valid Gemini API key in your environment")
                self.gemini_api_key = None
            elif not self.gemini_api_key.startswith('AIza'):
                print(f"⚠️ Warning: Gemini API key should start with 'AIza'")

    def validate_config(self) -> bool:
        """Validate configuration settings"""
        issues = []
        warnings = []

        # Critical issues
        if not self.gemini_api_key:
            issues.append("Missing valid Gemini API key - set GEMINI_API_KEY environment variable")

        if not self.opensearch_hosts:
            issues.append("Missing OpenSearch hosts configuration")

        if self.max_context_tokens <= 0:
            issues.append("Invalid max_context_tokens value")

        # Warnings
        if self.min_request_interval < 0.5:
            warnings.append("Very low rate limit interval - may hit API limits")

        # Display results
        if warnings:
            print("⚠️ Configuration warnings:")
            for warning in warnings:
                print(f"  - {warning}")

        if issues:
            print("❌ Configuration issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False

        print("✅ Configuration validation passed")
        return True

    def display_config(self):
        """Display current configuration (hiding sensitive data)"""
        print("\n📋 Current Configuration:")
        print(f"  OpenSearch: {self.opensearch_hosts}")
        print(f"  Embedding Model: {self.embedding_model}")
        
        if self.gemini_api_key:
            masked_key = f"{self.gemini_api_key[:10]}...{self.gemini_api_key[-4:]}"
            print(f"  Gemini API Key: {masked_key} ✅")
        else:
            print(f"  Gemini API Key: ❌ Not Set")
            
        print(f"  Search Method: {self.default_search_method}")
        print(f"  Max Context Tokens: {self.max_context_tokens}")
        print(f"  Rate Limit Interval: {self.min_request_interval}s")
        print(f"  Log Level: {self.log_level}")

    def wait_for_services(self, max_wait_time: int = 60):
        """Wait for required services to be available"""
        import time
        import requests
        from opensearchpy import OpenSearch
        
        print("🔄 Waiting for services to be ready...")
        
        # Wait for OpenSearch
        opensearch_ready = False
        start_time = time.time()
        
        while not opensearch_ready and (time.time() - start_time) < max_wait_time:
            try:
                host_config = self.opensearch_hosts[0]
                url = f"http://{host_config['host']}:{host_config['port']}/_cluster/health"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    opensearch_ready = True
                    print("✅ OpenSearch is ready")
                else:
                    print(f"⏳ OpenSearch not ready yet (status: {response.status_code})")
            except Exception as e:
                print(f"⏳ Waiting for OpenSearch... ({str(e)[:50]})")
            
            if not opensearch_ready:
                time.sleep(2)
        
        if not opensearch_ready:
            print("❌ OpenSearch failed to start within timeout period")
            return False
            
        return True