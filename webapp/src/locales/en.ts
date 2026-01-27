import { Translations } from './types';

/**
 * English translations
 */
export const en: Translations = {
  errors: {
    fileSizeTooLarge: (params) =>
      `File size too large (${params.fileSizeMB}MB). Maximum: ${params.maxSizeMB}MB`,
    fileTypeNotSupported: () =>
      `File type not supported. Allowed: JPG, PNG, WebP, GIF, BMP, TIFF`,
    maxAttachmentsReached: () => `Maximum 3 images`,
  },
  aria: {
    removeAttachment: () => `Remove attachment`,
    addAttachment: () => `Add attachment`,
    send: () => `Send`,
    closeViewer: () => `Close viewer`,
    like: () => `Like`,
    unlike: () => `Unlike`,
    moreOptions: () => `More options`,
    profileSettings: () => `Profile settings`,
  },
};
