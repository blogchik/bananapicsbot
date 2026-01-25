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
 * Update CSS variables for safe areas from Telegram WebApp API
 * Combines device safe area + Telegram content safe area (for Telegram UI elements)
 */
function updateSafeAreaCSSVariables(tg: NonNullable<typeof window.Telegram>['WebApp']): void {
  if (!tg) return;
  
  const root = document.documentElement;
  
  // Device safe area (notch, status bar, home indicator)
  const deviceTop = tg.safeAreaInset?.top || 0;
  const deviceRight = tg.safeAreaInset?.right || 0;
  const deviceBottom = tg.safeAreaInset?.bottom || 0;
  const deviceLeft = tg.safeAreaInset?.left || 0;
  
  // Telegram content safe area (Telegram header, bottom bar)
  const contentTop = tg.contentSafeAreaInset?.top || 0;
  const contentRight = tg.contentSafeAreaInset?.right || 0;
  const contentBottom = tg.contentSafeAreaInset?.bottom || 0;
  const contentLeft = tg.contentSafeAreaInset?.left || 0;
  
  // Combined safe area (max of device + content)
  const totalTop = Math.max(deviceTop, contentTop);
  const totalRight = Math.max(deviceRight, contentRight);
  const totalBottom = Math.max(deviceBottom, contentBottom);
  const totalLeft = Math.max(deviceLeft, contentLeft);
  
  // Set CSS variables
  root.style.setProperty('--tg-safe-area-top', `${totalTop}px`);
  root.style.setProperty('--tg-safe-area-right', `${totalRight}px`);
  root.style.setProperty('--tg-safe-area-bottom', `${totalBottom}px`);
  root.style.setProperty('--tg-safe-area-left', `${totalLeft}px`);
  
  // Also set content-only safe area for elements that need it
  root.style.setProperty('--tg-content-safe-top', `${contentTop}px`);
  root.style.setProperty('--tg-content-safe-bottom', `${contentBottom}px`);
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

      // Set CSS variables for safe areas (device + Telegram UI)
      updateSafeAreaCSSVariables(tg);

      // Listen to viewport changes to update safe areas
      tg.onEvent?.('viewportChanged', () => updateSafeAreaCSSVariables(tg));

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
