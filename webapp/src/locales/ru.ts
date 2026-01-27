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
  aria: {
    removeAttachment: () => `Удалить вложение`,
    addAttachment: () => `Добавить вложение`,
    send: () => `Отправить`,
    closeViewer: () => `Закрыть просмотр`,
    like: () => `Нравится`,
    unlike: () => `Убрать отметку`,
    moreOptions: () => `Дополнительные опции`,
    profileSettings: () => `Настройки профиля`,
  },
};
