import React from 'react';
import { SearchResult } from '../../types/api';
import { FileText, TrendingUp } from 'lucide-react';

interface SearchResultsProps {
  results: SearchResult[];
}

const SearchResults: React.FC<SearchResultsProps> = ({ results }) => {
  if (!results || results.length === 0) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 rounded-t-lg">
        <h3 className="text-sm font-medium text-gray-900 flex items-center">
          <FileText className="w-4 h-4 mr-2" />
          Source Documents ({results.length})
        </h3>
      </div>

      <div className="divide-y divide-gray-100">
        {results.map((result, index) => (
          <div key={result._id} className="p-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-start justify-between mb-2">
              <span className="text-xs font-medium text-gray-500">
                Source {index + 1}
              </span>
              <div className="flex items-center space-x-3 text-xs text-gray-500">
                <div className="flex items-center space-x-1">
                  <TrendingUp className="w-3 h-3" />
                  <span>Score: {result._score.toFixed(3)}</span>
                </div>
                <span>Vector: {result._vector_score.toFixed(3)}</span>
                <span>BM25: {result._bm25_score.toFixed(1)}</span>
              </div>
            </div>

            <p className="text-sm text-gray-700 leading-relaxed">
              {result._source.passage_text}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchResults;