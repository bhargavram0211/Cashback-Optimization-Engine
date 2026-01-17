import axios, { AxiosError } from 'axios';
import type { 
  SignupRequest, 
  LoginRequest, 
  AuthResponse, 
  UserInfoResponse,
  ApiError 
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
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - clear token and redirect to login
      localStorage.removeItem('session_token');
      localStorage.removeItem('auth_state');
      window.location.href = '/';
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
};
