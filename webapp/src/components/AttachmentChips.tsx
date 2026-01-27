import { memo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CloseIcon } from './Icons';
import { useAppStore } from '../store';
import { useTranslation } from '../hooks/useTranslation';
import { TranslationKey } from '../locales';
import type { Attachment } from '../types';

/**
 * AttachmentChips component - displays thumbnail previews above composer
 * Shows uploaded images for image-to-image generation
 */
export const AttachmentChips = memo(function AttachmentChips() {
  const { attachments, removeAttachment } = useAppStore();

  if (attachments.length === 0) return null;

  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="flex gap-2 px-4 pb-3 overflow-x-auto scrollbar-hide"
    >
      <AnimatePresence mode="popLayout">
        {attachments.map((attachment) => (
          <AttachmentChip
            key={attachment.id}
            attachment={attachment}
            onRemove={() => removeAttachment(attachment.id)}
          />
        ))}
      </AnimatePresence>
    </motion.div>
  );
});

interface AttachmentChipProps {
  attachment: Attachment;
  onRemove: () => void;
}

const AttachmentChip = memo(function AttachmentChip({
  attachment,
  onRemove,
}: AttachmentChipProps) {
  const { t } = useTranslation();
  const [isLoaded, setIsLoaded] = useState(false);

  return (
    <motion.div
      layout
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.8, opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="relative flex-shrink-0"
    >
      {/* Thumbnail image */}
      <div className="w-16 h-16 rounded-xl overflow-hidden bg-surface border border-white/10">
        {/* Loading skeleton */}
        {!isLoaded && (
          <div className="w-full h-full animate-pulse bg-surface-secondary" />
        )}
        {/* Image */}
        <img
          src={attachment.url}
          alt="Attachment"
          className={`w-full h-full object-cover ${!isLoaded ? 'hidden' : ''}`}
          onLoad={() => setIsLoaded(true)}
        />
      </div>

      {/* Remove button */}
      <motion.button
        whileTap={{ scale: 0.9 }}
        onClick={onRemove}
        className="absolute -top-1.5 -right-1.5 w-5 h-5 flex items-center justify-center rounded-full bg-dark-300 border border-white/10 shadow-lg"
        aria-label={t(TranslationKey.ARIA_REMOVE_ATTACHMENT)}
      >
        <CloseIcon size={12} className="text-white/70" />
      </motion.button>
    </motion.div>
  );
});
