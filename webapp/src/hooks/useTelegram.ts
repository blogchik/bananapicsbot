import { useEffect, useState, useCallback } from 'react';

/**
 * Hook for Telegram WebApp SDK integration
 * Provides theme params, haptic feedback, and other Telegram-specific features
 */
export function useTelegram() {
  const [isReady, setIsReady] = useState(false);
  const [user, setUser] = useState<{ id: number; firstName: string; lastName?: string } | null>(null);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;

    if (tg) {
      // Signal that the app is ready
      tg.ready();

      // Expand to full height
      tg.expand();

      // Set dark theme colors
      tg.setHeaderColor('#121212');
      tg.setBackgroundColor('#121212');

      // Extract user info if available
      if (tg.initDataUnsafe?.user) {
        setUser({
          id: tg.initDataUnsafe.user.id,
          firstName: tg.initDataUnsafe.user.first_name,
          lastName: tg.initDataUnsafe.user.last_name,
        });
      } else {
        // Mock user for development (test user ID from CLAUDE.md)
        setUser({
          id: 686980246,
          firstName: 'Test',
          lastName: 'User',
        });
      }

      setIsReady(true);
    } else {
      // Not in Telegram - mock data for web testing
      setUser({
        id: 686980246,
        firstName: 'Test',
        lastName: 'User',
      });
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
    user,
    hapticImpact,
    hapticNotification,
    hapticSelection,
    close,
    getSafeAreaInset,
    isTelegram: !!window.Telegram?.WebApp,
  };
}
