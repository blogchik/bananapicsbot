import { api } from './client';
import type { DailyDataPoint } from './admin';

// --- Types ---

export interface Payment {
  id: number;
  user_id: number;
  provider: string;
  currency: string;
  stars_amount: number;
  credits_amount: number;
  telegram_charge_id: string | null;
  is_refunded: boolean;
  created_at: string;
}

export interface PaginatedPayments {
  items: Payment[];
  total: number;
}

// --- API functions ---

export const paymentsApi = {
  getPayments: (offset = 0, limit = 50) =>
    api.get<PaginatedPayments>(
      `/admin/payments?offset=${offset}&limit=${limit}`,
    ),

  getPaymentsDaily: (days = 30) =>
    api.get<DailyDataPoint[]>(`/admin/payments/daily?days=${days}`),
};
