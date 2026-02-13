import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, AuthResponse } from '../types';
import { authAPI } from '../api/client';

interface AuthState {
  user: User | null;
  sessionToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User) => void;
  setSessionToken: (token: string) => void;
  clearError: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      sessionToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response: AuthResponse = await authAPI.login({ email, password });
          
          const user: User = {
            id: response.user_id,
            email: response.email,
            name: response.name,
            onboarding_completed: response.onboarding_completed,
          };

          set({
            user,
            sessionToken: response.session_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });

          // Store token in localStorage for API client
          localStorage.setItem('session_token', response.session_token);
        } catch (error: any) {
          console.error('Login error:', error);
          let errorMessage = 'Login failed. Please try again.';
          
          if (error.response?.data?.detail) {
            errorMessage = error.response.data.detail;
          } else if (error.message) {
            errorMessage = error.message;
          } else if (error.code === 'ERR_NETWORK') {
            errorMessage = 'Cannot connect to backend. Please check if the backend is running.';
          }
          
          set({
            isLoading: false,
            error: errorMessage,
            isAuthenticated: false,
          });
          throw error;
        }
      },

      signup: async (email: string, password: string, name?: string) => {
        set({ isLoading: true, error: null });
        try {
          const response: AuthResponse = await authAPI.signup({ email, password, name });
          
          const user: User = {
            id: response.user_id,
            email: response.email,
            name: response.name,
            onboarding_completed: response.onboarding_completed,
          };

          set({
            user,
            sessionToken: response.session_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });

          // Store token in localStorage for API client
          localStorage.setItem('session_token', response.session_token);
        } catch (error: any) {
          console.error('Signup error:', error);
          let errorMessage = 'Signup failed. Please try again.';
          
          if (error.response?.data?.detail) {
            errorMessage = error.response.data.detail;
          } else if (error.message) {
            errorMessage = error.message;
          } else if (error.code === 'ERR_NETWORK') {
            errorMessage = 'Cannot connect to backend. Please check if the backend is running.';
          }
          
          set({
            isLoading: false,
            error: errorMessage,
            isAuthenticated: false,
          });
          throw error;
        }
      },

      logout: async () => {
        try {
          const token = get().sessionToken;
          if (token) {
            await authAPI.logout();
          }
        } catch (error) {
          // Continue with logout even if API call fails
          console.error('Logout API call failed:', error);
        } finally {
          set({
            user: null,
            sessionToken: null,
            isAuthenticated: false,
            error: null,
          });
          localStorage.removeItem('session_token');
        }
      },

      setUser: (user: User) => {
        set({ user });
      },

      setSessionToken: (token: string) => {
        set({ sessionToken: token });
        localStorage.setItem('session_token', token);
      },

      clearError: () => {
        set({ error: null });
      },

      checkAuth: async () => {
        const token = get().sessionToken || localStorage.getItem('session_token');
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }

        set({ isLoading: true });
        try {
          const userInfo = await authAPI.getMe();
          const user: User = {
            id: userInfo.user_id,
            email: userInfo.email,
            name: userInfo.name,
            onboarding_completed: userInfo.onboarding_completed,
          };
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          // Token is invalid, clear auth state
          set({
            user: null,
            sessionToken: null,
            isAuthenticated: false,
            isLoading: false,
          });
          localStorage.removeItem('session_token');
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        sessionToken: state.sessionToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
