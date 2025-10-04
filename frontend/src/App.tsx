import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Header from './components/Layout/Header';
import ChatInterface from './components/Chat/ChatInterface';
import LoginPage from './components/Auth/LoginPage';
import searchAPI from './services/api';

const AppContent: React.FC = () => {
  const [isHealthy, setIsHealthy] = useState(false);
  const { isAuthenticated, isLoading } = useAuth();

  const checkHealth = async () => {
    try {
      const health = await searchAPI.health();
      setIsHealthy(health.workflow_ready);
    } catch (error) {
      setIsHealthy(false);
      console.error("Health check failed:", error);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      checkHealth();
      // Check health every 30 seconds
      const interval = setInterval(checkHealth, 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="flex items-center space-x-2">
          <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span className="text-lg text-gray-600">Loading...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Header isHealthy={isHealthy} onHealthCheck={checkHealth} />
      <div className="flex-1 flex flex-col min-h-0">
        <ChatInterface />
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;