import { useEffect, useState, useCallback } from 'react';

// Store initData globally for API calls
let globalInitData: string | null = null;

/**
 * Get the stored initData for API requests
 */
export function getInitData(): string | null {
  return globalInitData;
}

/**
 * Hook for Telegram WebApp SDK integration
 * Provides theme params, haptic feedback, initData validation, and other Telegram-specific features
 */
export function useTelegram() {
  const [isReady, setIsReady] = useState(false);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [user, setUser] = useState<{
    id: number;
    firstName: string;
    lastName?: string;
    username?: string;
    languageCode?: string;
  } | null>(null);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;

    // Check if running inside Telegram WebApp
    if (tg && tg.initData && tg.initData.length > 0) {
      // Store initData globally for API calls
      globalInitData = tg.initData;

      // Signal that the app is ready
      tg.ready();

      // Expand to full viewport height (critical for fullscreen)
      tg.expand();

      // Request fullscreen mode on mobile/tablet
      if (tg.isVersionAtLeast?.('6.1')) {
        tg.requestFullscreen?.();
      }

      // Lock orientation to portrait on mobile (if supported)
      if (tg.isVersionAtLeast?.('7.7')) {
        tg.lockOrientation?.();
      }

      // Set dark theme colors
      tg.setHeaderColor('#121212');
      tg.setBackgroundColor('#121212');

      // Enable closing confirmation to prevent accidental exits
      tg.enableClosingConfirmation();

      // Extract user info from initDataUnsafe (display only, validated on backend)
      if (tg.initDataUnsafe?.user) {
        setUser({
          id: tg.initDataUnsafe.user.id,
          firstName: tg.initDataUnsafe.user.first_name,
          lastName: tg.initDataUnsafe.user.last_name,
          username: tg.initDataUnsafe.user.username,
          languageCode: tg.initDataUnsafe.user.language_code,
        });
      }

      setIsAuthorized(true);
      setIsReady(true);
    } else {
      // Not in Telegram or no initData - block access
      globalInitData = null;
      setIsAuthorized(false);
      setIsReady(true);
    }
  }, []);

  // Haptic feedback helpers
  const hapticImpact = useCallback((style: 'light' | 'medium' | 'heavy' = 'light') => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred(style);
  }, []);

  const hapticNotification = useCallback((type: 'success' | 'error' | 'warning') => {
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred(type);
  }, []);

  const hapticSelection = useCallback(() => {
    window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
  }, []);

  // Close the app
  const close = useCallback(() => {
    window.Telegram?.WebApp?.close();
  }, []);

  // Open Telegram link
  const openTelegramLink = useCallback((url: string) => {
    window.Telegram?.WebApp?.openTelegramLink?.(url);
  }, []);

  // Get safe area insets for proper spacing on mobile devices
  const getSafeAreaInset = useCallback(() => {
    const tg = window.Telegram?.WebApp;
    
    // Use Telegram's safe area if available (Telegram WebApp API 6.2+)
    if (tg?.isVersionAtLeast?.('6.2') && tg.safeAreaInset) {
      return {
        top: tg.safeAreaInset.top || 0,
        right: tg.safeAreaInset.right || 0,
        bottom: tg.safeAreaInset.bottom || 0,
        left: tg.safeAreaInset.left || 0,
      };
    }
    
    // Fallback to CSS env variables
    const root = document.documentElement;
    const top = parseInt(getComputedStyle(root).getPropertyValue('--sat') || '0');
    const right = parseInt(getComputedStyle(root).getPropertyValue('--sar') || '0');
    const bottom = parseInt(getComputedStyle(root).getPropertyValue('--sab') || '0');
    const left = parseInt(getComputedStyle(root).getPropertyValue('--sal') || '0');
    
    return {
      top: top || 0,
      right: right || 0,
      bottom: bottom || 0,
      left: left || 0,
    };
  }, []);

  return {
    isReady,
    isAuthorized,
    user,
    initData: globalInitData,
    hapticImpact,
    hapticNotification,
    hapticSelection,
    close,
    openTelegramLink,
    getSafeAreaInset,
    isTelegram: !!window.Telegram?.WebApp,
  };
}
