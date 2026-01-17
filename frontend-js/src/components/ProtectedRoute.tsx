import React, { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { LoadingSpinner } from './LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading, checkAuth, sessionToken } = useAuthStore();

  useEffect(() => {
    // Check auth on mount if we have a token but aren't authenticated yet
    const token = sessionToken || localStorage.getItem('session_token');
    if (token && !isAuthenticated && !isLoading) {
      checkAuth();
    }
  }, [sessionToken, isAuthenticated, isLoading, checkAuth]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};
