/**
 * Translation keys enum for type-safe translations
 * Maps to keys in language-specific translation files
 */
export enum TranslationKey {
  // File upload errors
  FILE_SIZE_TOO_LARGE = 'errors.fileSizeTooLarge',
  FILE_TYPE_NOT_SUPPORTED = 'errors.fileTypeNotSupported',
  MAX_ATTACHMENTS_REACHED = 'errors.maxAttachmentsReached',

  // Aria labels for accessibility
  ARIA_REMOVE_ATTACHMENT = 'aria.removeAttachment',
  ARIA_ADD_ATTACHMENT = 'aria.addAttachment',
  ARIA_SEND = 'aria.send',
  ARIA_CLOSE_VIEWER = 'aria.closeViewer',
  ARIA_LIKE = 'aria.like',
  ARIA_UNLIKE = 'aria.unlike',
  ARIA_MORE_OPTIONS = 'aria.moreOptions',
  ARIA_PROFILE_SETTINGS = 'aria.profileSettings',
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
  aria: {
    removeAttachment: TranslationValue;
    addAttachment: TranslationValue;
    send: TranslationValue;
    closeViewer: TranslationValue;
    like: TranslationValue;
    unlike: TranslationValue;
    moreOptions: TranslationValue;
    profileSettings: TranslationValue;
  };
};
