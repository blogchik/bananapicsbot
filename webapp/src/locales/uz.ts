import { Translations } from './types';

/**
 * Uzbek translations
 */
export const uz: Translations = {
  errors: {
    fileSizeTooLarge: (params) =>
      `Fayl hajmi juda katta (${params.fileSizeMB}MB). Maksimal: ${params.maxSizeMB}MB`,
    fileTypeNotSupported: () =>
      `Fayl turi qo'llab-quvvatlanmaydi. Ruxsat etilgan: JPG, PNG, WebP, GIF, BMP, TIFF`,
    maxAttachmentsReached: () => `Maksimal 3 ta rasm qo'shish mumkin`,
  },
  aria: {
    removeAttachment: () => `Ilovani olib tashlash`,
    addAttachment: () => `Ilova qo'shish`,
    send: () => `Yuborish`,
    closeViewer: () => `Ko'ruvchini yopish`,
    like: () => `Yoqtirish`,
    unlike: () => `Yoqtirishni bekor qilish`,
    moreOptions: () => `Qo'shimcha parametrlar`,
    profileSettings: () => `Profil sozlamalari`,
  },
};
