import { createContext, ReactNode, useMemo } from 'react';
import { getTranslations, Translations, LanguageCode, DEFAULT_LANGUAGE } from '../locales';
import { useTelegram } from '../hooks/useTelegram';

/**
 * I18n context type
 */
interface I18nContextType {
  language: LanguageCode;
  translations: Translations;
}

/**
 * I18n context - provides current language and translations
 */
export const I18nContext = createContext<I18nContextType>({
  language: DEFAULT_LANGUAGE,
  translations: getTranslations(DEFAULT_LANGUAGE),
});

/**
 * I18n Provider - wraps app and provides translation context
 */
export function I18nProvider({ children }: { children: ReactNode }) {
  const { user } = useTelegram();

  const value = useMemo(() => {
    const languageCode = user?.languageCode || DEFAULT_LANGUAGE;
    const language = languageCode.toLowerCase().slice(0, 2) as LanguageCode;

    return {
      language: language in ['uz', 'ru', 'en'] ? language : DEFAULT_LANGUAGE,
      translations: getTranslations(languageCode),
    };
  }, [user?.languageCode]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
