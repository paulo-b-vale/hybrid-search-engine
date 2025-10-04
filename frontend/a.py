import os

# A dictionary where keys are file paths and values are the content for each file.
# This structure defines the entire directory and file layout.
files_to_create = {
    # --- Authentication Context ---
    "src/context/AuthContext.tsx": """
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import searchAPI from '../services/api';

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = !!user && !!token;

  // Check if user is authenticated on app load
  useEffect(() => {
    const checkAuth = async () => {
      const storedToken = localStorage.getItem('access_token');
      if (storedToken) {
        try {
          // Set the token in the API service
          searchAPI.setAuthToken(storedToken);
          const userData = await searchAPI.getCurrentUser();
          setUser(userData);
          setToken(storedToken);
        } catch (error) {
          // Token is invalid, remove it
          localStorage.removeItem('access_token');
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (username: string, password: string) => {
    try {
      setError(null);
      setIsLoading(true);
      
      const response = await searchAPI.login(username, password);
      
      localStorage.setItem('access_token', response.access_token);
      searchAPI.setAuthToken(response.access_token);
      
      setToken(response.access_token);
      setUser(response.user);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (username: string, email: string, password: string) => {
    try {
      setError(null);
      setIsLoading(true);
      
      await searchAPI.register(username, email, password);
      // After successful registration, automatically log in
      await login(username, password);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Registration failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await searchAPI.logout();
      }
    } catch (error) {
      // Even if logout fails on server, clear local state
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      searchAPI.setAuthToken(null);
      setToken(null);
      setUser(null);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    error,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
""",
    # --- API Service ---
    "src/services/api.ts": """
// Add these methods to your existing API service
class SearchAPI {
  private baseURL = 'http://localhost:8000';
  private authToken: string | null = null;

  setAuthToken(token: string | null) {
    this.authToken = token;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw {
        status: response.status,
        response: { data: errorData },
      };
    }

    return response.json();
  }

  async login(username: string, password: string) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async register(username: string, email: string, password: string) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  }

  async logout() {
    return this.request('/auth/logout', {
      method: 'POST',
    });
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  async health() {
    return this.request('/health');
  }

  async search(query: string, index_name: string, search_method?: string, num_results?: number) {
    return this.request('/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        index_name,
        search_method,
        num_results,
      }),
    });
  }
}

export default new SearchAPI();
""",
    # --- Login Page Component ---
    "src/components/Auth/LoginPage.tsx": """
import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

const LoginPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const { login, register, error, isLoading, clearError } = useAuth();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear validation error when user starts typing
    if (validationErrors[name]) {
      setValidationErrors(prev => ({ ...prev, [name]: '' }));
    }
    
    // Clear auth error
    if (error) {
      clearError();
    }
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.username.trim()) {
      errors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      errors.username = 'Username must be at least 3 characters';
    }

    if (!isLogin && !formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!isLogin && !/\\S+@\\S+\\.\\S+/.test(formData.email)) {
      errors.email = 'Please enter a valid email';
    }

    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }

    if (!isLogin && formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      if (isLogin) {
        await login(formData.username, formData.password);
      } else {
        await register(formData.username, formData.email, formData.password);
      }
    } catch (error) {
      // Error is handled in the auth context
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setFormData({ username: '', email: '', password: '', confirmPassword: '' });
    setValidationErrors({});
    clearError();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
            <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            {isLogin ? 'Sign in to your account' : 'Create your account'}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              type="button"
              onClick={toggleMode}
              className="font-medium text-blue-600 hover:text-blue-500 focus:outline-none"
            >
              {isLogin ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={formData.username}
                onChange={handleInputChange}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  validationErrors.username ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="Enter your username"
                disabled={isLoading}
              />
              {validationErrors.username && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.username}</p>
              )}
            </div>

            {!isLogin && (
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleInputChange}
                  className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                    validationErrors.email ? 'border-red-300' : 'border-gray-300'
                  } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                  placeholder="Enter your email"
                  disabled={isLoading}
                />
                {validationErrors.email && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.email}</p>
                )}
              </div>
            )}

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleInputChange}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  validationErrors.password ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="Enter your password"
                disabled={isLoading}
              />
              {validationErrors.password && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.password}</p>
              )}
            </div>

            {!isLogin && (
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  required
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                    validationErrors.confirmPassword ? 'border-red-300' : 'border-gray-300'
                  } placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                  placeholder="Confirm your password"
                  disabled={isLoading}
                />
                {validationErrors.confirmPassword && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.confirmPassword}</p>
                )}
              </div>
            )}
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {isLogin ? 'Signing in...' : 'Creating account...'}
                </div>
              ) : (
                isLogin ? 'Sign in' : 'Create account'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
""",
    # --- Header Component ---
    "src/components/Layout/Header.tsx": """
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
""",
    # --- App Component ---
    "src/App.tsx": """
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
        {/* You need to create this component or replace it */}
        {/* <ChatInterface /> */}
        <div className="p-4">Main application content goes here.</div>
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
"""
}

def create_project_structure():
    """
    Iterates through the files_to_create dictionary to create directories and files.
    """
    for filepath, content in files_to_create.items():
        # Extract the directory path from the filepath
        directory = os.path.dirname(filepath)

        # Create the directory if it doesn't already exist.
        # The `exist_ok=True` argument prevents an error if the directory is already there.
        if directory:
            os.makedirs(directory, exist_ok=True)

        # Write the content to the file.
        # The `with` statement ensures the file is properly closed even if errors occur.
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # The .strip() removes leading/trailing whitespace from the content string.
                f.write(content.strip())
            print(f"Successfully created: {filepath}")
        except IOError as e:
            print(f"Error creating file {filepath}: {e}")

# --- Main execution block ---
if __name__ == "__main__":
    print("Starting to create React auth structure...")
    create_project_structure()
    print("\nProject structure created successfully!")
    print("Please note: The 'ChatInterface' component in App.tsx is commented out.")
    print("You will need to create that component or replace it with your main app content.")

