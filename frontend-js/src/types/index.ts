// User types
export interface User {
  id: string;
  email: string;
  name?: string;
  onboarding_completed: boolean;
}

// Authentication request types
export interface SignupRequest {
  email: string;
  password: string;
  name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// Authentication response types
export interface AuthResponse {
  user_id: string;
  email: string;
  name?: string;
  session_token: string;
  onboarding_completed: boolean;
  message: string;
}

export interface UserInfoResponse {
  user_id: string;
  email: string;
  name?: string;
  onboarding_completed: boolean;
}

// API error type
export interface ApiError {
  detail: string;
}

// Form types
export interface SignupFormData {
  email: string;
  name: string;
  password: string;
  confirmPassword: string;
}

export interface LoginFormData {
  email: string;
  password: string;
}
