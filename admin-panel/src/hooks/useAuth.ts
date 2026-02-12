import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { authApi, type TelegramAuthData } from '@/api/auth';
import { setToken, clearToken } from '@/api/client';

export function useAuth() {
  const { token, admin, isAuthenticated, setAuth, setAdmin, logout: storeLogout } = useAuthStore();
  const navigate = useNavigate();

  const login = useCallback(
    async (telegramData: TelegramAuthData) => {
      const response = await authApi.login(telegramData);
      setToken(response.access_token);
      setAuth(response.access_token, response.admin);
      navigate('/', { replace: true });
    },
    [setAuth, navigate],
  );

  const logout = useCallback(() => {
    clearToken();
    storeLogout();
    navigate('/login', { replace: true });
  }, [storeLogout, navigate]);

  const validateSession = useCallback(async () => {
    if (!token) return false;
    try {
      const me = await authApi.getMe();
      setAdmin(me);
      return true;
    } catch {
      clearToken();
      storeLogout();
      return false;
    }
  }, [token, setAdmin, storeLogout]);

  return {
    token,
    admin,
    isAuthenticated,
    login,
    logout,
    validateSession,
  };
}
