import { api } from './client';

// --- Types ---

export interface AdminGeneration {
  id: number;
  public_id: string;
  user_telegram_id: number;
  model_key: string;
  model_name: string;
  prompt: string;
  status: string;
  cost: number | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface PaginatedGenerations {
  items: AdminGeneration[];
  total: number;
}

export interface QueueStatus {
  active: number;
  queued: number;
  running: number;
}

export interface GenerationsParams {
  offset?: number;
  limit?: number;
  status?: string;
}

// --- API functions ---

export const generationsApi = {
  getGenerations: (params: GenerationsParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.offset != null) searchParams.set('offset', String(params.offset));
    if (params.limit != null) searchParams.set('limit', String(params.limit));
    if (params.status) searchParams.set('status', params.status);
    const qs = searchParams.toString();
    return api.get<PaginatedGenerations>(
      `/admin/generations${qs ? `?${qs}` : ''}`,
    );
  },

  getQueueStatus: () =>
    api.get<QueueStatus>('/admin/generations/queue'),
};
