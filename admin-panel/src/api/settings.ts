import { api } from './client';

// --- Types ---

export interface SystemSetting {
  key: string;
  value: string;
  value_type: string;
  description: string | null;
  updated_at: string | null;
}

// --- API functions ---

export const settingsApi = {
  getSettings: () => api.get<SystemSetting[]>('/admin/settings'),

  updateSettings: (settings: Record<string, string>) =>
    api.patch<void>('/admin/settings', settings),
};
