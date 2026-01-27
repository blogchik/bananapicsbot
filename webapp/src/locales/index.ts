import { uz } from './uz';
import { ru } from './ru';
import { en } from './en';
import { LanguageCode, Translations } from './types';

export * from './types';

/**
 * All translations by language code
 */
export const translations: Record<LanguageCode, Translations> = {
  uz,
  ru,
  en,
};

/**
 * Default language code
 */
export const DEFAULT_LANGUAGE: LanguageCode = 'uz';

/**
 * Get translations for a language code
 * Falls back to default language if code not found
 */
export function getTranslations(languageCode?: string): Translations {
  const code = (languageCode || DEFAULT_LANGUAGE).toLowerCase().slice(0, 2) as LanguageCode;
  return translations[code] || translations[DEFAULT_LANGUAGE];
}
