import { api } from './client';

export interface TelegramAuthData {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
}

export interface AdminUser {
  telegram_id: number;
  username: string | null;
  first_name: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  admin: AdminUser;
  expires_at: string;
}

export const authApi = {
  login: (telegramData: TelegramAuthData) =>
    api.post<LoginResponse>('/admin/auth/login', telegramData),

  getMe: () => api.get<AdminUser>('/admin/auth/me'),
};
