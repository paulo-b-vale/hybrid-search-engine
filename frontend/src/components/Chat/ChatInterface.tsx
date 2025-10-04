import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage as ChatMessageType } from '../../types/api';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import searchAPI from '../../services/api';

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (query: string, settings: any) => {
    const userMessage: ChatMessageType = {
      id: Date.now().toString(),
      type: 'user',
      content: query,
      timestamp: new Date(),
    };

    const loadingMessage: ChatMessageType = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: 'Searching...',
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setIsLoading(true);

    try {
      console.log('ChatInterface: Making search request with settings:', settings);
      
      const response = await searchAPI.search(
        query,
        settings.index_name || 'passage_index',
        settings.search_method,
        settings.num_results
      );
      
      console.log('ChatInterface: Search response received:', response);

      const assistantMessage: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        searchResponse: response,
      };

      setMessages(prev => prev.slice(0, -1).concat(assistantMessage));
    } catch (error) {
      console.error('ChatInterface: Search error details:', {
        error,
        status: (error as any)?.status,
        response: (error as any)?.response
      });
      
      const errorMessage: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error while searching. Please try again.',
        timestamp: new Date(),
      };

      setMessages(prev => prev.slice(0, -1).concat(errorMessage));
      console.error('Search error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                Welcome to Hybrid Search AI
              </h2>
              <p className="text-gray-600 mb-6">
                Ask me anything! I'll search through documents and provide comprehensive answers with sources.
              </p>
              <div className="space-y-2 text-sm text-gray-500">
                <p>• Advanced hybrid search combining semantic and keyword matching</p>
                <p>• Quality validation and source attribution</p>
                <p>• Real-time processing insights</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
};

export default ChatInterface;