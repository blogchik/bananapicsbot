import { Translations } from './types';

/**
 * Russian translations
 */
export const ru: Translations = {
  errors: {
    fileSizeTooLarge: (params) =>
      `Размер файла слишком большой (${params.fileSizeMB}МБ). Максимум: ${params.maxSizeMB}МБ`,
    fileTypeNotSupported: () =>
      `Тип файла не поддерживается. Разрешены: JPG, PNG, WebP, GIF, BMP, TIFF`,
    maxAttachmentsReached: () => `Максимум 3 изображения`,
  },
};
