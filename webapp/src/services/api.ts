/**
 * API client for backend communication
 * Automatically includes Telegram initData header for authentication
 */

import { getInitData } from '../hooks/useTelegram';

// API base URL - will be configured via environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public detail: string,
    public data?: unknown
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

/**
 * Make an authenticated API request
 * Automatically includes X-Telegram-Init-Data header
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const initData = getInitData();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add Telegram initData header if available
  if (initData) {
    (headers as Record<string, string>)['X-Telegram-Init-Data'] = initData;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = 'An error occurred';
    let data: unknown;

    try {
      const errorData = await response.json();
      detail = errorData.detail || errorData.message || detail;
      data = errorData;
    } catch {
      // Response is not JSON
    }

    throw new ApiError(response.status, detail, data);
  }

  // Handle empty responses
  const contentType = response.headers.get('content-type');
  if (!contentType || !contentType.includes('application/json')) {
    return {} as T;
  }

  return response.json();
}

/**
 * API methods
 */
export const api = {
  // Users
  syncUser: (telegramId: number, referralCode?: string) =>
    request<{
      id: number;
      telegram_id: number;
      referral_code: string;
      referral_applied: boolean;
    }>('/users/sync', {
      method: 'POST',
      body: JSON.stringify({
        telegram_id: telegramId,
        referral_code: referralCode,
      }),
    }),

  getBalance: (telegramId: number) =>
    request<{ user_id: number; balance: number }>(
      `/users/${telegramId}/balance`
    ),

  getTrialStatus: (telegramId: number) =>
    request<{ user_id: number; trial_available: boolean; used_count: number }>(
      `/users/${telegramId}/trial`
    ),

  // Generations
  getGenerationPrice: (data: {
    telegram_id: number;
    model_id: number;
    size?: string;
    resolution?: string;
    quality?: string;
    aspect_ratio?: string;
    reference_count?: number;
  }) =>
    request<{ price: number; model_id: number }>('/generations/price', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  submitGeneration: (data: {
    telegram_id: number;
    model_id: number;
    prompt: string;
    size?: string;
    resolution?: string;
    quality?: string;
    aspect_ratio?: string;
    reference_urls?: string[];
    reference_file_ids?: string[];
  }) =>
    request<{
      request: { id: number; status: string };
      job_id: number;
      trial_used: boolean;
    }>('/generations/submit', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getActiveGeneration: (telegramId: number) =>
    request<{
      has_active: boolean;
      request_id?: number;
      public_id?: string;
      status?: string;
    }>(`/generations/active?telegram_id=${telegramId}`),

  getGeneration: (requestId: number, telegramId: number) =>
    request<{
      id: number;
      status: string;
      prompt: string;
      results?: Array<{ image_url: string }>;
    }>(`/generations/${requestId}?telegram_id=${telegramId}`),

  refreshGeneration: (requestId: number, telegramId: number) =>
    request<{
      id: number;
      status: string;
      results?: Array<{ image_url: string }>;
    }>(`/generations/${requestId}/refresh`, {
      method: 'POST',
      body: JSON.stringify({ telegram_id: telegramId }),
    }),

  getGenerationResults: (requestId: number, telegramId: number) =>
    request<string[]>(
      `/generations/${requestId}/results?telegram_id=${telegramId}`
    ),

  // Models
  getModels: () =>
    request<
      Array<{
        id: number;
        key: string;
        display_name: string;
        is_active: boolean;
      }>
    >('/models'),
};

export default api;
