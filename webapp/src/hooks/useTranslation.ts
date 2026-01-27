import { useContext, useCallback } from 'react';
import { I18nContext } from '../contexts/I18nContext';
import { TranslationKey } from '../locales';

/**
 * Hook for accessing translations
 * Returns translate function and current language
 */
export function useTranslation() {
  const { language, translations } = useContext(I18nContext);

  /**
   * Translate a key with optional parameters
   */
  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>): string => {
      // Navigate nested object by key path (e.g., "errors.fileSizeTooLarge")
      const keys = key.split('.');
      let value: unknown = translations;

      for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
          value = (value as Record<string, unknown>)[k];
        } else {
          return key; // Return key if translation not found
        }
      }

      // If value is a function, call it with params
      if (typeof value === 'function') {
        const fn = value as (params: Record<string, string | number>) => string;
        return fn(params || {});
      }

      // If value is a string, return it
      if (typeof value === 'string') {
        return value;
      }

      // Fallback to key if value is not string or function
      return key;
    },
    [translations]
  );

  return { t, language };
}
