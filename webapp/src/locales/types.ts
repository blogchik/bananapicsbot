/**
 * Translation keys enum for type-safe translations
 * Maps to keys in language-specific translation files
 */
export enum TranslationKey {
  // File upload errors
  FILE_SIZE_TOO_LARGE = 'errors.fileSizeTooLarge',
  FILE_TYPE_NOT_SUPPORTED = 'errors.fileTypeNotSupported',
  MAX_ATTACHMENTS_REACHED = 'errors.maxAttachmentsReached',
}

/**
 * Type for translation strings with optional placeholders
 */
export type TranslationValue = string | ((params: Record<string, string | number>) => string);

/**
 * Supported language codes
 */
export type LanguageCode = 'uz' | 'ru' | 'en';

/**
 * Translation dictionary type
 */
export type Translations = {
  errors: {
    fileSizeTooLarge: TranslationValue;
    fileTypeNotSupported: TranslationValue;
    maxAttachmentsReached: TranslationValue;
  };
};
