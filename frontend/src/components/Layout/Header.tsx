import React from 'react';
import { useAuth } from '../../context/AuthContext';

interface HeaderProps {
  isHealthy: boolean;
  onHealthCheck: () => void;
}

const Header: React.FC<HeaderProps> = ({ isHealthy, onHealthCheck }) => {
  const { user, logout, isAuthenticated } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">
              Hybrid Search API
            </h1>
            <div className="ml-4 flex items-center">
              <div className={`h-3 w-3 rounded-full ${isHealthy ? 'bg-green-400' : 'bg-red-400'}`}></div>
              <span className="ml-2 text-sm text-gray-600">
                {isHealthy ? 'Healthy' : 'Degraded'}
              </span>
              <button
                onClick={onHealthCheck}
                className="ml-2 text-sm text-blue-600 hover:text-blue-800"
              >
                Check
              </button>
            </div>
          </div>

          {isAuthenticated && (
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <span className="text-sm font-medium text-blue-600">
                    {user?.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <span className="text-sm text-gray-700">{user?.username}</span>
              </div>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md hover:bg-gray-100"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;