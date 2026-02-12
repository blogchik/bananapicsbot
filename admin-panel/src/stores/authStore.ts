import { create } from 'zustand';

export interface AdminUser {
  telegram_id: number;
  username: string | null;
  first_name: string;
}

interface AuthState {
  token: string | null;
  admin: AdminUser | null;
  isAuthenticated: boolean;
  setAuth: (token: string, admin: AdminUser) => void;
  setAdmin: (admin: AdminUser) => void;
  logout: () => void;
}

const TOKEN_KEY = 'admin_token';
const ADMIN_KEY = 'admin_user';

function loadInitialState(): { token: string | null; admin: AdminUser | null } {
  const token = localStorage.getItem(TOKEN_KEY);
  const adminStr = localStorage.getItem(ADMIN_KEY);
  let admin: AdminUser | null = null;

  if (adminStr) {
    try {
      admin = JSON.parse(adminStr);
    } catch {
      admin = null;
    }
  }

  return { token, admin };
}

const initial = loadInitialState();

export const useAuthStore = create<AuthState>((set) => ({
  token: initial.token,
  admin: initial.admin,
  isAuthenticated: !!initial.token,

  setAuth: (token: string, admin: AdminUser) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(ADMIN_KEY, JSON.stringify(admin));
    set({ token, admin, isAuthenticated: true });
  },

  setAdmin: (admin: AdminUser) => {
    localStorage.setItem(ADMIN_KEY, JSON.stringify(admin));
    set({ admin });
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(ADMIN_KEY);
    set({ token: null, admin: null, isAuthenticated: false });
  },
}));
