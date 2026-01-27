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
};
