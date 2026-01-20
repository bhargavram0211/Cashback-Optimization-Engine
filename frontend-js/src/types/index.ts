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

// Report types
export interface CategoryBreakdown {
  category: string;
  transaction_count: number;
  total_spent: number;
  lost_savings: number;
  actual_cashback: number;
  potential_cashback: number;
}

export interface RecommendedCard {
  provider: string;
  card_name: string;
  times_recommended: number;
  total_potential_savings: number;
  avg_savings_per_transaction: number;
}

export interface SavingsSummary {
  total_spent: number;
  total_lost_savings: number;
  total_earned: number;
  transaction_count: number;
  total_potential: number;
}

export interface SavingsReport {
  summary: SavingsSummary;
  category_breakdown: CategoryBreakdown[];
  top_recommendation: RecommendedCard | null;
}

// Card types
export interface RewardRule {
  bucket: string;
  multiplier: number;
}

export interface CardProduct {
  id: string;
  provider: string;
  card_name: string;
  base_reward_rate: number;
  image_url: string | null;
  benefits_url: string | null;
  reward_rules: RewardRule[];
}

export interface UnidentifiedCard {
  id: string;
  plaid_account_id: string;
  official_name: string;
  mask: string;
  created_at: string;
}

export interface IdentifyCardResponse {
  status: string;
  user_card_id: string;
  card_product: string;
  message: string;
}

// Plaid types
export interface ConnectSandboxResponse {
  plaid_item_id: string;
  institution_name: string;
  transactions_synced: number;
  cards_found: number;
  message: string;
}

export interface PlaidItemResponse {
  id: string;
  user_id: string;
  institution_id: string | null;
  last_cursor: string | null;
  created_at: string;
  updated_at: string;
}

export interface SyncResponse {
  item_id: string;
  transactions_added: number;
  transactions_updated: number;
  transactions_removed: number;
  accounts_synced: number;
  cursor_updated: boolean;
}

export interface OptimizeResponse {
  status: string;
  total_transactions: number;
  optimized: number;
  skipped?: number;
  skipped_non_analyzable?: number;
  skipped_no_bucket?: number;
  total_actual_cashback: number;
  total_potential_cashback: number;
  total_lost_savings: number;
  average_lost_per_transaction?: number;
  message?: string;
}

// Plaid Link types
export interface LinkTokenResponse {
  link_token: string;
  expiration: string;
}

export interface ExchangeTokenRequest {
  public_token: string;
  institution_id: string;
  institution_name: string;
}

export interface ExchangeTokenResponse {
  plaid_item_id: string;
  institution_name: string;
  transactions_synced: number;
  cards_found: number;
  message: string;
}

// Plaid Link callback types
export interface PlaidLinkOnSuccessMetadata {
  institution: {
    institution_id: string;
    name: string;
  };
  accounts: Array<{
    id: string;
    name: string;
    mask: string;
    type: string;
    subtype: string;
  }>;
  link_session_id: string;
}

export interface PlaidLinkOnExitMetadata {
  institution?: {
    institution_id: string;
    name: string;
  } | null;
  status?: string | null;
}

export type PlaidLinkExitReason =
  | 'USER_EXIT'
  | 'INSTITUTION_ERROR'
  | 'INVALID_CREDENTIALS'
  | 'ITEM_LOGIN_REQUIRED'
  | 'RATE_LIMIT_EXCEEDED'
  | 'USER_PERMISSION_DENIED'
  | 'USER_OAUTH_ACTION_REQUIRED'
  | 'ERROR'
  | 'OTHER';
