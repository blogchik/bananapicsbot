import { api } from './client';

// --- Types ---

export interface DashboardStats {
  total_users: number;
  active_users_7d: number;
  active_users_30d: number;
  new_users_today: number;
  new_users_week: number;
  new_users_month: number;
  banned_users: number;
  total_generations: number;
  completed_generations: number;
  failed_generations: number;
  success_rate: number;
  total_deposits: number;
  today_deposits: number;
  week_deposits: number;
  month_deposits: number;
  total_refunded: number;
  total_spent: number;
  net_revenue: number;
  by_model: Record<string, any>;
  total_payments: number;
  completed_payments: number;
  payment_success_rate: number;
}

export interface DailyDataPoint {
  date: string;
  count: number;
  amount?: number;
}

export interface GenerationDailyPoint {
  date: string;
  total: number;
  completed: number;
  failed: number;
}

export interface ModelBreakdownItem {
  model_key: string;
  model_name: string;
  count: number;
  credits: number;
}

export interface WavespeedModelBreakdown {
  model_key: string;
  model_name: string;
  total: number;
  completed: number;
  failed: number;
  success_rate: number;
  credits: number;
}

export interface WavespeedRecentGeneration {
  id: number;
  public_id: string;
  telegram_id: number;
  model_key: string;
  model_name: string;
  status: string;
  cost: number;
  prompt: string;
  created_at: string | null;
  completed_at: string | null;
}

export interface WavespeedStatus {
  balance: {
    amount: number;
    currency: string;
  };
  provider_status: 'online' | 'degraded' | 'offline';
  generations_24h: {
    total: number;
    completed: number;
    failed: number;
    success_rate: number;
  };
  generations_7d: {
    total: number;
    completed: number;
    failed: number;
    success_rate: number;
  };
  queue: {
    pending: number;
    running: number;
  };
  models: WavespeedModelBreakdown[];
  recent_generations: WavespeedRecentGeneration[];
}

// --- API functions ---

export const adminApi = {
  getStats: (days?: number) =>
    api.get<DashboardStats>(
      `/admin/stats${days != null ? `?days=${days}` : ''}`,
    ),

  getUsersDaily: (days?: number) =>
    api.get<DailyDataPoint[]>(
      `/admin/charts/users-daily${days != null ? `?days=${days}` : ''}`,
    ),

  getGenerationsDaily: (days?: number) =>
    api.get<GenerationDailyPoint[]>(
      `/admin/charts/generations-daily${days != null ? `?days=${days}` : ''}`,
    ),

  getRevenueDaily: (days?: number) =>
    api.get<DailyDataPoint[]>(
      `/admin/charts/revenue-daily${days != null ? `?days=${days}` : ''}`,
    ),

  getModelsBreakdown: () =>
    api.get<ModelBreakdownItem[]>('/admin/charts/models-breakdown'),

  getWavespeedStatus: () =>
    api.get<WavespeedStatus>('/admin/wavespeed/status'),
};
