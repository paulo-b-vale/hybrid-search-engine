import React from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Bot, Clock, Zap, DollarSign } from 'lucide-react';
import { ChatMessage as ChatMessageType } from '../../types/api';
import SearchResults from './SearchResults';

interface ChatMessageProps {
  message: ChatMessageType;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.type === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`flex max-w-4xl ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-blue-600' : 'bg-gray-600'
          }`}>
            {isUser ? (
              <User className="w-4 h-4 text-white" />
            ) : (
              <Bot className="w-4 h-4 text-white" />
            )}
          </div>
        </div>

        <div className={`flex-1 ${isUser ? 'text-right' : 'text-left'}`}>
          <div className={`inline-block max-w-full ${
            isUser 
              ? 'bg-blue-600 text-white rounded-lg px-4 py-2'
              : 'bg-gray-100 rounded-lg px-4 py-2'
          }`}>
            {message.isLoading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-pulse-slow w-2 h-2 bg-gray-400 rounded-full"></div>
                <div className="animate-pulse-slow w-2 h-2 bg-gray-400 rounded-full" style={{ animationDelay: '0.2s' }}></div>
                <div className="animate-pulse-slow w-2 h-2 bg-gray-400 rounded-full" style={{ animationDelay: '0.4s' }}></div>
                <span className="ml-2 text-gray-600">Searching...</span>
              </div>
            ) : (
              <ReactMarkdown className="prose prose-sm max-w-none">
                {message.content}
              </ReactMarkdown>
            )}
          </div>

          {message.searchResponse && !message.isLoading && (
            <div className="mt-4 space-y-4">
              {/* Search Metadata */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-3">
                  <div className="flex items-center space-x-1">
                    <Clock className="w-4 h-4" />
                    <span>{message.searchResponse.total_processing_time.toFixed(2)}s</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Zap className="w-4 h-4" />
                    <span>{message.searchResponse.total_tokens} tokens</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <DollarSign className="w-4 h-4" />
                    <span>${message.searchResponse.cost_estimate.toFixed(6)}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <span className="font-medium">Quality:</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      message.searchResponse.quality_score > 0.8 
                        ? 'bg-green-100 text-green-800'
                        : message.searchResponse.quality_score > 0.6
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {(message.searchResponse.quality_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Method and Results Count */}
                <div className="text-sm text-gray-500">
                  Method: <span className="font-medium">{message.searchResponse.method}</span> • 
                  Results: <span className="font-medium">{message.searchResponse.num_results}</span>
                </div>
              </div>

              {/* Search Results */}
              <SearchResults results={message.searchResponse.search_results} />

              {/* Workflow Messages */}
              {message.searchResponse.workflow_messages.length > 0 && (
                <details className="bg-gray-50 border border-gray-200 rounded-lg">
                  <summary className="px-4 py-2 cursor-pointer text-sm font-medium text-gray-700 hover:bg-gray-100">
                    Workflow Steps ({message.searchResponse.workflow_messages.length})
                  </summary>
                  <div className="px-4 pb-4 pt-2 space-y-1">
                    {message.searchResponse.workflow_messages.map((msg, idx) => (
                      <div key={idx} className="text-xs text-gray-600 font-mono">
                        {msg}
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          )}

          <div className="text-xs text-gray-500 mt-2">
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;