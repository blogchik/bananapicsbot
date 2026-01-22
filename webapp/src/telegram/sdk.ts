import type { WebApp, TelegramUser, ThemeParams, HapticFeedback } from './types'

/**
 * Get the Telegram WebApp instance
 * Returns null if not running inside Telegram
 */
export function getWebApp(): WebApp | null {
  if (typeof window === 'undefined') return null
  return window.Telegram?.WebApp ?? null
}

/**
 * Check if running inside Telegram WebApp
 */
export function isTelegramWebApp(): boolean {
  const webApp = getWebApp()
  return webApp !== null && !!webApp.initData
}

/**
 * Initialize the WebApp and expand to full height
 */
export function initWebApp(): WebApp | null {
  const webApp = getWebApp()
  if (!webApp) return null

  // Signal that the app is ready
  webApp.ready()

  // Expand to full height
  webApp.expand()

  // Set header color to match theme
  if (webApp.themeParams.header_bg_color) {
    webApp.setHeaderColor(webApp.themeParams.header_bg_color)
  }

  return webApp
}

/**
 * Get init data string for backend validation
 */
export function getInitData(): string {
  return getWebApp()?.initData ?? ''
}

/**
 * Get user data from init data
 */
export function getUser(): TelegramUser | null {
  return getWebApp()?.initDataUnsafe?.user ?? null
}

/**
 * Get user ID
 */
export function getUserId(): number | null {
  return getUser()?.id ?? null
}

/**
 * Get theme params
 */
export function getThemeParams(): ThemeParams {
  return getWebApp()?.themeParams ?? {}
}

/**
 * Get color scheme (light/dark)
 */
export function getColorScheme(): 'light' | 'dark' {
  return getWebApp()?.colorScheme ?? 'light'
}

/**
 * Check if dark mode is active
 */
export function isDarkMode(): boolean {
  return getColorScheme() === 'dark'
}

/**
 * Apply Telegram theme to CSS variables
 */
export function applyThemeToCss(): void {
  const theme = getThemeParams()
  const root = document.documentElement

  // Set CSS variables from theme params
  if (theme.bg_color) {
    root.style.setProperty('--tg-theme-bg-color', theme.bg_color)
  }
  if (theme.secondary_bg_color) {
    root.style.setProperty('--tg-theme-secondary-bg-color', theme.secondary_bg_color)
  }
  if (theme.text_color) {
    root.style.setProperty('--tg-theme-text-color', theme.text_color)
  }
  if (theme.hint_color) {
    root.style.setProperty('--tg-theme-hint-color', theme.hint_color)
  }
  if (theme.link_color) {
    root.style.setProperty('--tg-theme-link-color', theme.link_color)
  }
  if (theme.button_color) {
    root.style.setProperty('--tg-theme-button-color', theme.button_color)
  }
  if (theme.button_text_color) {
    root.style.setProperty('--tg-theme-button-text-color', theme.button_text_color)
  }
  if (theme.header_bg_color) {
    root.style.setProperty('--tg-theme-header-bg-color', theme.header_bg_color)
  }
  if (theme.accent_text_color) {
    root.style.setProperty('--tg-theme-accent-text-color', theme.accent_text_color)
  }
  if (theme.section_bg_color) {
    root.style.setProperty('--tg-theme-section-bg-color', theme.section_bg_color)
  }
  if (theme.section_header_text_color) {
    root.style.setProperty('--tg-theme-section-header-text-color', theme.section_header_text_color)
  }
  if (theme.subtitle_text_color) {
    root.style.setProperty('--tg-theme-subtitle-text-color', theme.subtitle_text_color)
  }
  if (theme.destructive_text_color) {
    root.style.setProperty('--tg-theme-destructive-text-color', theme.destructive_text_color)
  }

  // Set dark mode class
  if (isDarkMode()) {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

/**
 * Haptic feedback wrapper
 */
export const haptic: HapticFeedback = {
  impactOccurred: (style) => {
    getWebApp()?.HapticFeedback?.impactOccurred(style)
  },
  notificationOccurred: (type) => {
    getWebApp()?.HapticFeedback?.notificationOccurred(type)
  },
  selectionChanged: () => {
    getWebApp()?.HapticFeedback?.selectionChanged()
  },
}

/**
 * Main button controls
 */
export const mainButton = {
  show: (text: string, onClick: () => void) => {
    const webApp = getWebApp()
    if (!webApp) return

    webApp.MainButton.setText(text)
    webApp.MainButton.onClick(onClick)
    webApp.MainButton.show()
  },

  hide: () => {
    getWebApp()?.MainButton?.hide()
  },

  setText: (text: string) => {
    getWebApp()?.MainButton?.setText(text)
  },

  showProgress: () => {
    getWebApp()?.MainButton?.showProgress()
  },

  hideProgress: () => {
    getWebApp()?.MainButton?.hideProgress()
  },

  enable: () => {
    getWebApp()?.MainButton?.enable()
  },

  disable: () => {
    getWebApp()?.MainButton?.disable()
  },
}

/**
 * Back button controls
 */
export const backButton = {
  show: (onClick: () => void) => {
    const webApp = getWebApp()
    if (!webApp) return

    webApp.BackButton.onClick(onClick)
    webApp.BackButton.show()
  },

  hide: () => {
    getWebApp()?.BackButton?.hide()
  },
}

/**
 * Open a URL in the browser
 */
export function openLink(url: string, tryInstantView = false): void {
  getWebApp()?.openLink(url, { try_instant_view: tryInstantView })
}

/**
 * Open a Telegram link (t.me)
 */
export function openTelegramLink(url: string): void {
  getWebApp()?.openTelegramLink(url)
}

/**
 * Open an invoice for payment
 */
export function openInvoice(url: string): Promise<'paid' | 'cancelled' | 'failed' | 'pending'> {
  return new Promise((resolve) => {
    const webApp = getWebApp()
    if (!webApp) {
      resolve('failed')
      return
    }

    webApp.openInvoice(url, (status) => {
      resolve(status)
    })
  })
}

/**
 * Show a popup alert
 */
export function showAlert(message: string): Promise<void> {
  return new Promise((resolve) => {
    const webApp = getWebApp()
    if (!webApp) {
      alert(message)
      resolve()
      return
    }

    webApp.showAlert(message, resolve)
  })
}

/**
 * Show a confirmation dialog
 */
export function showConfirm(message: string): Promise<boolean> {
  return new Promise((resolve) => {
    const webApp = getWebApp()
    if (!webApp) {
      resolve(window.confirm(message))
      return
    }

    webApp.showConfirm(message, resolve)
  })
}

/**
 * Close the WebApp
 */
export function closeWebApp(): void {
  getWebApp()?.close()
}

/**
 * Get start_param from deep link
 */
export function getStartParam(): string | undefined {
  return getWebApp()?.initDataUnsafe?.start_param
}
