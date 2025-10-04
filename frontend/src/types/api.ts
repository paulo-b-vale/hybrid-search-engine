export interface SearchRequest {
  query: string;
  index_name: string;
  search_method?: string;
  num_results?: number;
}

export interface SearchResult {
  _index: string;
  _id: string;
  _score: number;
  _source: {
    passage_text: string;
  };
  _vector_score: number;
  _bm25_score: number;
}

export interface ContentAnalysis {
  num_documents: number;
  avg_text_length: number;
  avg_word_count: number;
  score_stats: {
    min: number;
    max: number;
    mean: number;
    std: number;
  };
  top_keywords: [string, number][];
  content_diversity: number;
  total_unique_words: number;
  analysis_timestamp: string;
}

export interface ValidationResults {
  quality_score: number;
  issues: string[];
  validation_passed: boolean;
  retry_recommended: boolean;
  source_references: number;
  relevance_ratio: number;
  quality_factors: number[];
}

export interface SearchResponse {
  query: string;
  answer: string;
  method: string;
  num_results: number;
  search_results: SearchResult[];
  content_analysis: ContentAnalysis;
  similarity_analysis: Record<string, any>;
  validation_results: ValidationResults;
  step_times: Record<string, number>;
  total_processing_time: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_estimate: number;
  workflow_messages: string[];
  quality_score: number;
  error?: string;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  searchResponse?: SearchResponse;
  isLoading?: boolean;
}

export interface HealthResponse {
  status: string;
  workflow_ready: boolean;
  timestamp: string;
  message: string;
}