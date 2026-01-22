import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import uz from './locales/uz.json'
import ru from './locales/ru.json'
import en from './locales/en.json'

// Get initial language from Telegram user or localStorage
function getInitialLanguage(): string {
  // Try localStorage first
  const stored = localStorage.getItem('bananapics-user')
  if (stored) {
    try {
      const parsed = JSON.parse(stored)
      if (parsed.state?.language) {
        return parsed.state.language
      }
    } catch {
      // Ignore parse errors
    }
  }

  // Try Telegram user language
  const tgUser = window.Telegram?.WebApp?.initDataUnsafe?.user
  if (tgUser?.language_code) {
    const code = tgUser.language_code.toLowerCase()
    if (code === 'uz') return 'uz'
    if (code === 'ru') return 'ru'
    return 'en'
  }

  return 'uz' // Default to Uzbek
}

i18n.use(initReactI18next).init({
  resources: {
    uz: { translation: uz },
    ru: { translation: ru },
    en: { translation: en },
  },
  lng: getInitialLanguage(),
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false, // React already escapes
  },
  react: {
    useSuspense: false,
  },
})

export default i18n

// Helper to change language
export function changeLanguage(lang: 'uz' | 'ru' | 'en') {
  i18n.changeLanguage(lang)
}

// Available languages
export const languages = [
  { code: 'uz', name: "O'zbek", nativeName: "O'zbekcha" },
  { code: 'ru', name: 'Russian', nativeName: 'Русский' },
  { code: 'en', name: 'English', nativeName: 'English' },
] as const

export type LanguageCode = (typeof languages)[number]['code']
