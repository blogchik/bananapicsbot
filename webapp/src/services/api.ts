/**
 * API client for backend communication
 * Automatically includes Telegram initData header for authentication
 */

import { getInitData } from '../hooks/useTelegram';
import { logger } from './logger';

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
  const method = options.method || 'GET';
  const startTime = performance.now();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add Telegram initData header if available
  if (initData) {
    (headers as Record<string, string>)['X-Telegram-Init-Data'] = initData;
  }

  // Log request start
  logger.api.info(`${method} ${endpoint}`, {
    hasInitData: !!initData,
    body: options.body ? JSON.parse(options.body as string) : undefined,
  });

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    const duration = Math.round(performance.now() - startTime);

    // Check content type before attempting to parse
    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');

    // Parse response body once to avoid "body already consumed" error
    let data: unknown;
    if (isJson) {
      try {
        data = await response.json();
      } catch {
        // JSON parsing failed - data remains undefined
      }
    }

    if (!response.ok) {
      const detail =
        (data as Record<string, unknown>)?.detail as string ||
        (data as Record<string, unknown>)?.message as string ||
        'An error occurred';

      logger.api.error(`${method} ${endpoint} failed`, {
        status: response.status,
        detail,
        data,
        duration: `${duration}ms`,
      });

      throw new ApiError(response.status, detail, data);
    }

    // Handle empty/non-JSON responses
    if (!isJson || data === undefined) {
      logger.api.error(`${method} ${endpoint} returned no data`, {
        status: response.status,
        contentType,
        duration: `${duration}ms`,
      });
      throw new ApiError(
        response.status,
        'API returned no data when data was expected',
        { contentType }
      );
    }

    logger.api.debug(`${method} ${endpoint} completed`, {
      status: response.status,
      duration: `${duration}ms`,
      response: data,
    });

    return data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    const duration = Math.round(performance.now() - startTime);
    logger.api.error(`${method} ${endpoint} network error`, {
      error: error instanceof Error ? error.message : String(error),
      duration: `${duration}ms`,
    });

    throw error;
  }
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
      `/users/${encodeURIComponent(telegramId)}/balance`
    ),

  getTrialStatus: (telegramId: number) =>
    request<{ user_id: number; trial_available: boolean; used_count: number }>(
      `/users/${encodeURIComponent(telegramId)}/trial`
    ),

  // Generations
  listGenerations: (telegramId: number, limit = 50, offset = 0) => {
    const params = new URLSearchParams({
      telegram_id: String(telegramId),
      limit: String(limit),
      offset: String(offset),
    });
    return request<{
      items: Array<{
        id: number;
        public_id: string;
        prompt: string;
        status: string;
        mode: 't2i' | 'i2i';
        model_key: string;
        model_name: string;
        aspect_ratio: string | null;
        size: string | null;
        resolution: string | null;
        quality: string | null;
        cost: number | null;
        result_urls: string[];
        reference_urls: string[];
        error_message: string | null;
        created_at: string;
        completed_at: string | null;
      }>;
      total: number;
      limit: number;
      offset: number;
    }>(`/generations?${params}`);
  },

  getGenerationPrice: (data: {
    telegram_id: number;
    model_id: number;
    size?: string;
    resolution?: string;
    quality?: string;
    aspect_ratio?: string;
    reference_count?: number;
    is_image_to_image?: boolean;
  }) =>
    request<{
      model_id: number;
      model_key: string;
      price_credits: number;
      price_usd: number;
      is_dynamic: boolean;
      cached: boolean;
    }>('/generations/price', {
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
    input_fidelity?: string;
    reference_urls?: string[];
    reference_file_ids?: string[];
  }) =>
    request<{
      request: {
        id: number;
        public_id: string;
        status: string;
        prompt: string;
        created_at: string;
      };
      job_id: number;
      provider_job_id: string | null;
      trial_used: boolean;
    }>('/generations/submit', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getActiveGeneration: (telegramId: number) => {
    const params = new URLSearchParams({ telegram_id: String(telegramId) });
    return request<{
      has_active: boolean;
      request_id?: number;
      public_id?: string;
      status?: string;
    }>(`/generations/active?${params}`);
  },

  getGeneration: (requestId: number, telegramId: number) => {
    const params = new URLSearchParams({ telegram_id: String(telegramId) });
    return request<{
      id: number;
      status: string;
      prompt: string;
      results?: Array<{ image_url: string }>;
    }>(`/generations/${encodeURIComponent(requestId)}?${params}`);
  },

  refreshGeneration: (requestId: number, telegramId: number) =>
    request<{
      id: number;
      status: string;
      results?: Array<{ image_url: string }>;
    }>(`/generations/${requestId}/refresh`, {
      method: 'POST',
      body: JSON.stringify({ telegram_id: telegramId }),
    }),

  getGenerationResults: (requestId: number, telegramId: number) => {
    const params = new URLSearchParams({ telegram_id: String(telegramId) });
    return request<string[]>(
      `/generations/${encodeURIComponent(requestId)}/results?${params}`
    );
  },

  // Models
  getModels: () =>
    request<
      Array<{
        model: {
          id: number;
          key: string;
          name: string;
          provider: string;
          supports_text_to_image: boolean;
          supports_image_to_image: boolean;
          supports_reference: boolean;
          supports_aspect_ratio: boolean;
          supports_style: boolean;
          is_active: boolean;
          options: {
            supports_size: boolean;
            supports_aspect_ratio: boolean;
            supports_resolution: boolean;
            supports_quality: boolean;
            supports_input_fidelity: boolean;
            quality_stars: number | null;
            avg_duration_seconds_min: number | null;
            avg_duration_seconds_max: number | null;
            avg_duration_text: string | null;
            size_options: string[] | null;
            aspect_ratio_options: string[] | null;
            resolution_options: string[] | null;
            quality_options: string[] | null;
            input_fidelity_options: string[] | null;
          };
        };
        prices: Array<{
          id: number;
          model_id: number;
          currency: string;
          unit_price: number;
          is_active: boolean;
        }>;
      }>
    >('/models'),
};

export default api;
