import { api } from './client';

// --- Types ---

export interface AdminUser {
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  photo_url: string | null;
  language_code: string | null;
  is_active: boolean;
  is_banned: boolean;
  ban_reason: string | null;
  trial_remaining: number;
  balance: number;
  referrer_id: number | null;
  referral_code: string | null;
  referral_count: number;
  generation_count: number;
  total_spent: number;
  total_deposits: number;
  created_at: string;
  last_active_at: string | null;
}

export interface UserListResponse {
  users: AdminUser[];
  total: number;
  offset: number;
  limit: number;
}

export interface UserGeneration {
  id: number;
  model_key: string;
  model_name: string;
  prompt: string;
  status: string;
  credits_charged: number;
  created_at: string;
}

export interface UserPayment {
  id: number;
  stars_amount: number;
  credits_amount: number;
  status: string;
  created_at: string;
}

export interface CreditAdjustmentResponse {
  telegram_id: number;
  amount: number;
  old_balance: number;
  new_balance: number;
  reason: string | null;
}

// --- API functions ---

export const usersApi = {
  searchUsers: (query?: string, offset = 0, limit = 50) => {
    const params = new URLSearchParams();
    if (query) params.set('query', query);
    params.set('offset', String(offset));
    params.set('limit', String(limit));
    return api.get<UserListResponse>(`/admin/users?${params.toString()}`);
  },

  getUser: (telegramId: number) =>
    api.get<AdminUser>(`/admin/users/${telegramId}`),

  banUser: (telegramId: number, reason?: string) =>
    api.post<void>(`/admin/users/${telegramId}/ban`, reason ? { reason } : undefined),

  unbanUser: (telegramId: number) =>
    api.post<void>(`/admin/users/${telegramId}/unban`),

  adjustCredits: (telegramId: number, amount: number, reason: string) =>
    api.post<CreditAdjustmentResponse>(`/admin/credits`, {
      telegram_id: telegramId,
      amount,
      reason,
    }),

  getUserGenerations: (telegramId: number, limit = 10) =>
    api.get<UserGeneration[]>(
      `/admin/users/${telegramId}/generations?limit=${limit}`,
    ),

  getUserPayments: (telegramId: number, limit = 10) =>
    api.get<UserPayment[]>(
      `/admin/users/${telegramId}/payments?limit=${limit}`,
    ),
};
