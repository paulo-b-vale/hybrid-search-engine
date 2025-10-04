import React, { useState, KeyboardEvent } from 'react';
import { Send, Settings } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (query: string, settings: SearchSettings) => void;
  isLoading: boolean;
}

interface SearchSettings {
  index_name: string;
  search_method?: string;
  num_results: number;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState<SearchSettings>({
    index_name: 'passage_index',
    search_method: undefined,
    num_results: 5,
  });

  const handleSubmit = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim(), settings);
      setMessage('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white">
      {showSettings && (
        <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-0">
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Index Name
              </label>
              <input
                type="text"
                value={settings.index_name}
                onChange={(e) => setSettings(prev => ({ ...prev, index_name: e.target.value }))}
                className="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div className="flex-1 min-w-0">
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Search Method
              </label>
              <select
                value={settings.search_method || ''}
                onChange={(e) => setSettings(prev => ({ 
                  ...prev, 
                  search_method: e.target.value || undefined 
                }))}
                className="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">Auto</option>
                <option value="hybrid">Hybrid</option>
                <option value="semantic">Semantic</option>
                <option value="bm25">BM25</option>
                <option value="multi_stage">Multi-stage</option>
              </select>
            </div>

            <div className="w-24">
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Results
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={settings.num_results}
                onChange={(e) => setSettings(prev => ({ 
                  ...prev, 
                  num_results: parseInt(e.target.value) || 5 
                }))}
                className="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      )}

      <div className="p-4">
        <div className="flex items-end space-x-3">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`p-2 rounded-lg transition-colors ${
              showSettings 
                ? 'bg-blue-100 text-blue-600' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title="Search Settings"
          >
            <Settings className="w-4 h-4" />
          </button>

          <div className="flex-1 relative">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything..."
              rows={1}
              className="w-full resize-none border border-gray-300 rounded-lg px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              style={{ minHeight: '44px', maxHeight: '120px' }}
            />

            <button
              onClick={handleSubmit}
              disabled={!message.trim() || isLoading}
              className="absolute right-2 bottom-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;