import { api } from './client';

// --- Types ---

export interface Broadcast {
  id: number;
  public_id: string;
  admin_id: number;
  content_type: string;
  text: string | null;
  media_file_id: string | null;
  inline_button_text: string | null;
  inline_button_url: string | null;
  filter_type: string;
  status: string;
  total_users: number;
  sent_count: number;
  failed_count: number;
  blocked_count: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface BroadcastStatus {
  public_id: string;
  status: string;
  total_users: number;
  sent_count: number;
  failed_count: number;
  blocked_count: number;
  progress_percent: number;
  started_at: string | null;
  completed_at: string | null;
}

export interface BroadcastListResponse {
  broadcasts: Broadcast[];
  total: number;
  offset: number;
  limit: number;
}

export interface CreateBroadcastInput {
  content_type: string;
  text: string;
  filter_type: string;
  inline_button_text?: string;
  inline_button_url?: string;
}

export interface UsersCountResponse {
  count: number;
  filter_type: string;
}

// --- API functions ---

export const broadcastsApi = {
  listBroadcasts: (limit = 20, offset = 0) =>
    api.get<BroadcastListResponse>(
      `/admin/broadcasts?limit=${limit}&offset=${offset}`,
    ),

  getBroadcastStatus: (publicId: string) =>
    api.get<BroadcastStatus>(`/admin/broadcasts/${publicId}`),

  createBroadcast: (data: CreateBroadcastInput) =>
    api.post<Broadcast>('/admin/broadcasts', data),

  startBroadcast: (publicId: string) =>
    api.post<void>(`/admin/broadcasts/${publicId}/start`),

  cancelBroadcast: (publicId: string) =>
    api.post<void>(`/admin/broadcasts/${publicId}/cancel`),

  getUsersCount: (filterType: string) =>
    api.get<UsersCountResponse>(
      `/admin/broadcasts/users-count?filter_type=${encodeURIComponent(filterType)}`,
    ),
};
