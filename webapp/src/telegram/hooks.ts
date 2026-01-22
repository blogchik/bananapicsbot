import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import type { TelegramUser, ThemeParams } from './types'
import {
  getWebApp,
  getUser,
  getInitData,
  getThemeParams,
  getColorScheme,
  haptic,
  mainButton,
  backButton,
  isTelegramWebApp,
} from './sdk'

/**
 * Hook to get Telegram WebApp instance
 */
export function useTelegram() {
  const webApp = getWebApp()

  return {
    webApp,
    isReady: isTelegramWebApp(),
    initData: getInitData(),
    user: getUser(),
    colorScheme: getColorScheme(),
    themeParams: getThemeParams(),
    platform: webApp?.platform ?? 'unknown',
    version: webApp?.version ?? '0.0',
  }
}

/**
 * Hook to get Telegram user
 */
export function useTelegramUser(): TelegramUser | null {
  return getUser()
}

/**
 * Hook to get user ID
 */
export function useUserId(): number | null {
  return getUser()?.id ?? null
}

/**
 * Hook to get init data for API calls
 */
export function useInitData(): string {
  return getInitData()
}

/**
 * Hook to get theme params
 */
export function useThemeParams(): ThemeParams {
  const [theme, setTheme] = useState<ThemeParams>(getThemeParams())

  useEffect(() => {
    const webApp = getWebApp()
    if (!webApp) return

    const handleThemeChange = () => {
      setTheme(getThemeParams())
    }

    webApp.onEvent('themeChanged', handleThemeChange)
    return () => {
      webApp.offEvent('themeChanged', handleThemeChange)
    }
  }, [])

  return theme
}

/**
 * Hook to get color scheme with updates
 */
export function useColorScheme(): 'light' | 'dark' {
  const [scheme, setScheme] = useState<'light' | 'dark'>(getColorScheme())

  useEffect(() => {
    const webApp = getWebApp()
    if (!webApp) return

    const handleThemeChange = () => {
      setScheme(getColorScheme())
    }

    webApp.onEvent('themeChanged', handleThemeChange)
    return () => {
      webApp.offEvent('themeChanged', handleThemeChange)
    }
  }, [])

  return scheme
}

/**
 * Hook for haptic feedback
 */
export function useHaptic() {
  return {
    impact: useCallback((style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft' = 'medium') => {
      haptic.impactOccurred(style)
    }, []),

    notification: useCallback((type: 'error' | 'success' | 'warning') => {
      haptic.notificationOccurred(type)
    }, []),

    selection: useCallback(() => {
      haptic.selectionChanged()
    }, []),
  }
}

/**
 * Hook for Telegram Main Button
 */
export function useMainButton(text: string, onClick: () => void, enabled = true) {
  useEffect(() => {
    if (!text) {
      mainButton.hide()
      return
    }

    mainButton.show(text, onClick)

    if (enabled) {
      mainButton.enable()
    } else {
      mainButton.disable()
    }

    return () => {
      mainButton.hide()
    }
  }, [text, onClick, enabled])

  return {
    setText: mainButton.setText,
    showProgress: mainButton.showProgress,
    hideProgress: mainButton.hideProgress,
    enable: mainButton.enable,
    disable: mainButton.disable,
  }
}

/**
 * Hook for Telegram Back Button with React Router integration
 */
export function useBackButton(show = true) {
  const navigate = useNavigate()
  const location = useLocation()

  const handleBack = useCallback(() => {
    haptic.impactOccurred('light')

    // Check if we can go back in history
    if (window.history.length > 1) {
      navigate(-1)
    } else {
      // Go to home as fallback
      navigate('/')
    }
  }, [navigate])

  useEffect(() => {
    // Don't show back button on home page
    const isHome = location.pathname === '/'

    if (show && !isHome) {
      backButton.show(handleBack)
    } else {
      backButton.hide()
    }

    return () => {
      backButton.hide()
    }
  }, [show, handleBack, location.pathname])
}

/**
 * Hook to get viewport height (accounts for Telegram UI)
 */
export function useViewportHeight(): number {
  const [height, setHeight] = useState(getWebApp()?.viewportStableHeight ?? window.innerHeight)

  useEffect(() => {
    const webApp = getWebApp()
    if (!webApp) return

    const handleViewportChange = () => {
      setHeight(webApp.viewportStableHeight)
    }

    webApp.onEvent('viewportChanged', handleViewportChange)
    return () => {
      webApp.offEvent('viewportChanged', handleViewportChange)
    }
  }, [])

  return height
}

/**
 * Hook to handle closing confirmation
 */
export function useClosingConfirmation(enabled: boolean) {
  useEffect(() => {
    const webApp = getWebApp()
    if (!webApp) return

    if (enabled) {
      webApp.enableClosingConfirmation()
    } else {
      webApp.disableClosingConfirmation()
    }

    return () => {
      webApp.disableClosingConfirmation()
    }
  }, [enabled])
}
