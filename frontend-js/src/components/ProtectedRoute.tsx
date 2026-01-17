import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { LoadingSpinner } from './LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireOnboarding?: boolean; // If true, redirect to onboarding if not completed
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requireOnboarding = true 
}) => {
  const { isAuthenticated, isLoading, checkAuth, sessionToken, user } = useAuthStore();
  const location = useLocation();

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

  // Check onboarding status (but allow access to /onboarding route itself)
  if (requireOnboarding && user && !user.onboarding_completed && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />;
  }

  return <>{children}</>;
};
