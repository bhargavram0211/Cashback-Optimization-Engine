import axios, { AxiosError } from 'axios';
import type { 
  SignupRequest, 
  LoginRequest, 
  AuthResponse, 
  UserInfoResponse,
  ApiError,
  SavingsReport,
  CardProduct,
  UnidentifiedCard,
  IdentifyCardResponse,
  ConnectSandboxResponse,
  OptimizeResponse,
  PlaidItemResponse,
  SyncResponse,
  LinkTokenResponse,
  ExchangeTokenRequest,
  ExchangeTokenResponse
} from '../types';

const API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('session_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    // Handle 204 No Content responses
    if (response.status === 204) {
      return response;
    }
    return response;
  },
  (error: AxiosError<ApiError>) => {
    // Only redirect on 401 if we're not already on the landing page
    // AND only for auth-related endpoints (not for protected resource endpoints)
    if (error.response?.status === 401) {
      const url = error.config?.url || '';
      const isAuthEndpoint = url.includes('/auth/');
      
      // For non-auth endpoints, clear token but let component handle the error
      // Only redirect if it's an auth endpoint failure (login/signup) or if we're on a protected route
      if (!isAuthEndpoint) {
        // Clear token but don't redirect - let the component show error
        localStorage.removeItem('session_token');
        localStorage.removeItem('auth_state');
        // Reject the error so component can handle it
        return Promise.reject(error);
      }
      
      // For auth endpoints, redirect to login
      localStorage.removeItem('session_token');
      localStorage.removeItem('auth_state');
      if (window.location.pathname !== '/') {
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  }
);

// Authentication API methods
export const authAPI = {
  signup: async (data: SignupRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/signup', data);
    return response.data;
  },

  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/login', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },

  getMe: async (): Promise<UserInfoResponse> => {
    const response = await apiClient.get<UserInfoResponse>('/auth/me');
    return response.data;
  },

  markOnboardingComplete: async (): Promise<{ message: string; onboarding_completed: boolean }> => {
    const response = await apiClient.patch<{ message: string; onboarding_completed: boolean }>('/auth/onboarding-complete');
    return response.data;
  },
};

// Reports API methods
export const reportsAPI = {
  getSavingsReport: async (userId: string): Promise<SavingsReport> => {
    const response = await apiClient.get<SavingsReport>(`/reports/savings/${userId}`);
    return response.data;
  },
};

// Cards API methods
export const cardsAPI = {
  getCardProducts: async (): Promise<CardProduct[]> => {
    const response = await apiClient.get<CardProduct[]>('/cards/card-products');
    return response.data;
  },

  getUnidentifiedCards: async (userId: string): Promise<UnidentifiedCard[]> => {
    const response = await apiClient.get<UnidentifiedCard[]>(
      `/cards/user-cards/unidentified?user_id=${userId}`
    );
    return response.data;
  },

  identifyCard: async (
    userCardId: string,
    cardProductId: string
  ): Promise<IdentifyCardResponse> => {
    const response = await apiClient.post<IdentifyCardResponse>(
      `/cards/user-cards/${userCardId}/identify?card_product_id=${cardProductId}`
    );
    return response.data;
  },
};

// Plaid API methods
export const plaidAPI = {
  connectSandbox: async (): Promise<ConnectSandboxResponse> => {
    const response = await apiClient.post<ConnectSandboxResponse>('/plaid/connect-sandbox');
    return response.data;
  },

  createLinkToken: async (): Promise<LinkTokenResponse> => {
    const response = await apiClient.post<LinkTokenResponse>('/plaid/create-link-token');
    return response.data;
  },

  exchangeToken: async (data: ExchangeTokenRequest): Promise<ExchangeTokenResponse> => {
    const response = await apiClient.post<ExchangeTokenResponse>('/plaid/exchange-token', data);
    return response.data;
  },
};

// Items API methods
export const itemsAPI = {
  getUserPlaidItems: async (userId: string): Promise<PlaidItemResponse[]> => {
    const response = await apiClient.get<PlaidItemResponse[]>(`/items?user_id=${userId}`);
    return response.data;
  },

  deletePlaidItem: async (itemId: string): Promise<void> => {
    await apiClient.delete(`/items/${itemId}`);
  },
};

// Sync API methods
export const syncAPI = {
  syncTransactions: async (itemId: string): Promise<SyncResponse> => {
    const response = await apiClient.post<SyncResponse>(`/sync/${itemId}`);
    return response.data;
  },
};

// Optimize API methods
export const optimizeAPI = {
  optimizeAll: async (): Promise<OptimizeResponse> => {
    const response = await apiClient.post<OptimizeResponse>('/optimize');
    return response.data;
  },
};
