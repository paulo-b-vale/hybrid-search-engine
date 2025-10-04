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