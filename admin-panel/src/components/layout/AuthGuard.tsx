import { useEffect, useState, type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { authApi } from '@/api/auth';
import { clearToken } from '@/api/client';

interface AuthGuardProps {
  children: ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, setAdmin, logout } = useAuthStore();
  const [isValidating, setIsValidating] = useState(true);
  const [isValid, setIsValid] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      setIsValidating(false);
      return;
    }

    let cancelled = false;

    async function validate() {
      try {
        const me = await authApi.getMe();
        if (!cancelled) {
          setAdmin(me);
          setIsValid(true);
        }
      } catch {
        if (!cancelled) {
          clearToken();
          logout();
        }
      } finally {
        if (!cancelled) {
          setIsValidating(false);
        }
      }
    }

    validate();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, setAdmin, logout]);

  if (isValidating) {
    return (
      <div className="min-h-screen bg-dark-500 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-banana-500/30 border-t-banana-500 rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground">Verifying session...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !isValid) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
