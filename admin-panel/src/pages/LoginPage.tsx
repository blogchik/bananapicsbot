import { useEffect, useRef, useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { authApi, type TelegramAuthData } from '@/api/auth';
import { setToken } from '@/api/client';
import { Shield, AlertCircle, ShieldX, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

declare global {
  interface Window {
    onTelegramAuth: (user: TelegramAuthData) => void;
  }
}

export function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, setAuth } = useAuthStore();
  const widgetRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'not_admin' | 'general' | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const botUsername = import.meta.env.VITE_BOT_USERNAME;

  const handleTelegramAuth = useCallback(
    async (user: TelegramAuthData) => {
      setIsLoading(true);
      setError(null);
      setErrorType(null);
      try {
        const response = await authApi.login(user);
        setToken(response.access_token);
        setAuth(response.access_token, response.admin);
        navigate('/', { replace: true });
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : String(err);
        const isNotAdmin = errorMessage.toLowerCase().includes('not an admin') ||
          errorMessage.toLowerCase().includes('403') ||
          errorMessage.toLowerCase().includes('forbidden');

        if (isNotAdmin) {
          setErrorType('not_admin');
          setError('You are not an admin');
        } else {
          setErrorType('general');
          setError(errorMessage || 'Authentication failed');
        }
      } finally {
        setIsLoading(false);
      }
    },
    [navigate, setAuth],
  );

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
      return;
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (!botUsername || !widgetRef.current) return;

    window.onTelegramAuth = handleTelegramAuth;

    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', botUsername);
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-radius', '8');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    script.async = true;

    widgetRef.current.innerHTML = '';
    widgetRef.current.appendChild(script);

    return () => {
      delete (window as Partial<Window>).onTelegramAuth;
    };
  }, [botUsername, handleTelegramAuth]);

  return (
    <div className="min-h-screen bg-dark-500 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background gradient effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-banana-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-banana-500/3 rounded-full blur-3xl" />
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-banana-500/20 to-transparent" />
      </div>

      {/* Login card */}
      <div className="relative w-full max-w-md animate-fade-in">
        <div className="bg-surface border border-surface-lighter/50 rounded-2xl p-8 shadow-elevated backdrop-blur-sm">
          {/* Logo section */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent-muted mb-4">
              <Shield className="w-8 h-8 text-banana-500" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-1">
              <span className="text-banana-500">Banana</span>Pics
            </h1>
            <p className="text-sm font-medium text-muted-foreground tracking-wide uppercase">
              Admin Panel
            </p>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3 mb-8">
            <div className="flex-1 h-px bg-surface-lighter" />
            <span className="text-xs text-muted uppercase tracking-widest">Sign In</span>
            <div className="flex-1 h-px bg-surface-lighter" />
          </div>

          {/* Telegram Widget */}
          <div className="flex flex-col items-center gap-4">
            {isLoading ? (
              <div className="flex items-center gap-3 text-muted-foreground">
                <div className="w-5 h-5 border-2 border-banana-500/30 border-t-banana-500 rounded-full animate-spin" />
                <span className="text-sm">Authenticating...</span>
              </div>
            ) : botUsername ? (
              <>
                <p className="text-sm text-muted-foreground text-center mb-2">
                  Sign in with your Telegram account
                </p>
                <div ref={widgetRef} id="telegram-login-widget" className="flex justify-center" />
              </>
            ) : (
              <div className="flex items-center gap-2 text-warning bg-warning-muted rounded-lg px-4 py-3 w-full">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span className="text-sm">
                  Bot username not configured. Set <code className="font-mono text-xs bg-dark-300 px-1.5 py-0.5 rounded">VITE_BOT_USERNAME</code> environment variable.
                </span>
              </div>
            )}

            {error && (
              <div className={cn(
                'w-full rounded-xl p-4 animate-slide-in-up',
                errorType === 'not_admin'
                  ? 'bg-gradient-to-br from-destructive/10 to-destructive/5 border border-destructive/20'
                  : 'bg-destructive-muted'
              )}>
                {errorType === 'not_admin' ? (
                  <div className="flex flex-col items-center text-center gap-3">
                    <div className="w-14 h-14 rounded-2xl bg-destructive/10 flex items-center justify-center">
                      <ShieldX className="w-7 h-7 text-destructive" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-destructive mb-1">
                        Access Denied
                      </h3>
                      <p className="text-sm text-destructive/80">
                        Siz admin emassiz / You are not an admin
                      </p>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Your Telegram ID is not in the admin list.
                      <br />
                      Contact the bot owner for access.
                    </p>
                  </div>
                ) : (
                  <div className="flex items-start gap-2 text-destructive">
                    <XCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">{error}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer note */}
          <div className="mt-8 pt-6 border-t border-surface-lighter/50">
            <p className="text-xs text-muted text-center">
              Only authorized administrators can access this panel.
              <br />
              Contact the bot owner for access.
            </p>
          </div>
        </div>

        {/* Subtle glow underneath the card */}
        <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-3/4 h-8 bg-banana-500/5 blur-2xl rounded-full" />
      </div>
    </div>
  );
}
