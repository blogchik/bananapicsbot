import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import type { TelegramUser, ThemeParams } from '@/telegram/types'
import {
  initWebApp,
  applyThemeToCss,
  getUser,
  getInitData,
  getThemeParams,
  getColorScheme,
  isTelegramWebApp,
} from '@/telegram/sdk'

interface TelegramContextValue {
  isReady: boolean
  isLoading: boolean
  user: TelegramUser | null
  initData: string
  themeParams: ThemeParams
  colorScheme: 'light' | 'dark'
  platform: string
}

const TelegramContext = createContext<TelegramContextValue | null>(null)

interface TelegramProviderProps {
  children: ReactNode
}

/**
 * Access Denied Screen - shown when not opened from Telegram
 */
function AccessDeniedScreen() {
  const { t } = useTranslation()
  
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-6">
      <div className="text-center max-w-md">
        {/* Telegram Logo */}
        <div className="mb-6 flex justify-center">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <svg className="w-12 h-12 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.18 1.897-.962 6.502-1.359 8.627-.168.9-.5 1.201-.82 1.23-.697.064-1.226-.461-1.901-.903-1.056-.692-1.653-1.123-2.678-1.799-1.185-.781-.417-1.21.258-1.911.177-.184 3.247-2.977 3.307-3.23.007-.032.015-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.139-5.062 3.345-.479.329-.913.489-1.302.481-.428-.009-1.252-.242-1.865-.442-.751-.244-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.831-2.529 6.998-3.015 3.333-1.386 4.025-1.627 4.477-1.635.099-.002.321.023.465.141.121.099.154.232.17.325.015.093.034.305.019.472z"/>
            </svg>
          </div>
        </div>
        
        {/* Title */}
        <h1 className="text-2xl font-bold text-white mb-3">
          {t('access.title', 'Telegram Required')}
        </h1>
        
        {/* Description */}
        <p className="text-gray-300 mb-6 leading-relaxed">
          {t('access.description', 'This application can only be accessed through Telegram. Please open it from the Telegram app.')}
        </p>
        
        {/* Instructions */}
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-5 text-left border border-white/10">
          <p className="text-sm text-gray-400 mb-3">{t('access.howToOpen', 'How to open:')}</p>
          <ol className="text-sm text-gray-300 space-y-2">
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-medium">1</span>
              <span>{t('access.step1', 'Open Telegram app')}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-medium">2</span>
              <span>{t('access.step2', 'Find our bot @bananapicsbot')}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-medium">3</span>
              <span>{t('access.step3', 'Click the "Open App" button')}</span>
            </li>
          </ol>
        </div>
        
        {/* Open Telegram Button */}
        <a
          href="https://t.me/bananapicsbot"
          target="_blank"
          rel="noopener noreferrer"
          className="mt-6 inline-flex items-center gap-2 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-xl transition-colors"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.18 1.897-.962 6.502-1.359 8.627-.168.9-.5 1.201-.82 1.23-.697.064-1.226-.461-1.901-.903-1.056-.692-1.653-1.123-2.678-1.799-1.185-.781-.417-1.21.258-1.911.177-.184 3.247-2.977 3.307-3.23.007-.032.015-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.139-5.062 3.345-.479.329-.913.489-1.302.481-.428-.009-1.252-.242-1.865-.442-.751-.244-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.831-2.529 6.998-3.015 3.333-1.386 4.025-1.627 4.477-1.635.099-.002.321.023.465.141.121.099.154.232.17.325.015.093.034.305.019.472z"/>
          </svg>
          {t('access.openTelegram', 'Open in Telegram')}
        </a>
      </div>
    </div>
  )
}

export function TelegramProvider({ children }: TelegramProviderProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [contextValue, setContextValue] = useState<TelegramContextValue>({
    isReady: false,
    isLoading: true,
    user: null,
    initData: '',
    themeParams: {},
    colorScheme: 'light',
    platform: 'unknown',
  })

  useEffect(() => {
    // Initialize WebApp
    const webApp = initWebApp()

    // Apply theme to CSS variables
    applyThemeToCss()

    // Update context
    setContextValue({
      isReady: isTelegramWebApp(),
      isLoading: false,
      user: getUser(),
      initData: getInitData(),
      themeParams: getThemeParams(),
      colorScheme: getColorScheme(),
      platform: webApp?.platform ?? 'unknown',
    })

    setIsLoading(false)

    // Listen for theme changes
    if (webApp) {
      const handleThemeChange = () => {
        applyThemeToCss()
        setContextValue((prev) => ({
          ...prev,
          themeParams: getThemeParams(),
          colorScheme: getColorScheme(),
        }))
      }

      webApp.onEvent('themeChanged', handleThemeChange)
      return () => {
        webApp.offEvent('themeChanged', handleThemeChange)
      }
    }
  }, [])

  // Show loading state while initializing
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-tg-bg">
        <div className="w-10 h-10 border-3 border-tg-hint/20 border-t-accent-purple rounded-full animate-spin" />
      </div>
    )
  }

  // Block access if not opened from Telegram WebApp
  // In production, always require Telegram
  // In development, allow bypass for testing
  if (!contextValue.isReady) {
    // Check if DEV mode and user explicitly wants to bypass (via query param)
    const allowDevBypass = import.meta.env.DEV && window.location.search.includes('dev=true')
    
    if (!allowDevBypass) {
      return <AccessDeniedScreen />
    }
    
    console.warn('⚠️ Telegram WebApp not detected. Running in DEV bypass mode.')
  }

  return (
    <TelegramContext.Provider value={contextValue}>
      {children}
    </TelegramContext.Provider>
  )
}

export function useTelegramContext(): TelegramContextValue {
  const context = useContext(TelegramContext)
  if (!context) {
    throw new Error('useTelegramContext must be used within TelegramProvider')
  }
  return context
}
