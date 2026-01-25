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

      // Expand to full height
      tg.expand();

      // Set dark theme colors
      tg.setHeaderColor('#121212');
      tg.setBackgroundColor('#121212');

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

  // Get safe area insets (bottom padding for iOS)
  const getSafeAreaInset = useCallback(() => {
    // Try to get from CSS env variables
    const computedStyle = getComputedStyle(document.documentElement);
    const bottomInset = computedStyle.getPropertyValue('--tg-viewport-stable-height');
    return {
      bottom: bottomInset ? 20 : 0, // Add padding if in Telegram
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
