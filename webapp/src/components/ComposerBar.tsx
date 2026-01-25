import { memo, useRef, useCallback, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PlusIcon, SendIcon, SpinnerIcon, CreditIcon, ImageIcon, CameraIcon } from './Icons';
import { AttachmentChips } from './AttachmentChips';
import { useAppStore } from '../store';
import { useTelegram } from '../hooks/useTelegram';

// File validation constants
const ALLOWED_IMAGE_TYPES = [
  'image/jpeg',
  'image/jpg',
  'image/png',
  'image/webp',
  'image/gif',
  'image/bmp',
  'image/tiff',
];

const ALLOWED_EXTENSIONS = '.jpg,.jpeg,.png,.webp,.gif,.bmp,.tiff,.tif';

const MAX_FILE_SIZE_MB = 20;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024; // 20MB in bytes

// Validate file type and size
function validateImageFile(file: File): { valid: boolean; error?: string } {
  // Check file type
  const fileType = file.type.toLowerCase();
  const fileName = file.name.toLowerCase();
  const extension = fileName.substring(fileName.lastIndexOf('.'));

  const isValidType = ALLOWED_IMAGE_TYPES.includes(fileType) ||
    ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff', '.tif'].includes(extension);

  if (!isValidType) {
    return {
      valid: false,
      error: `Fayl turi qo'llab-quvvatlanmaydi. Ruxsat etilgan: JPG, PNG, WebP, GIF, BMP, TIFF`,
    };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE_BYTES) {
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
    return {
      valid: false,
      error: `Fayl hajmi juda katta (${fileSizeMB}MB). Maksimal: ${MAX_FILE_SIZE_MB}MB`,
    };
  }

  return { valid: true };
}

/**
 * ComposerBar component - bottom input bar for creating generations
 * Features prompt input, attachment handling, and send button
 */
export const ComposerBar = memo(function ComposerBar() {
  const {
    prompt,
    setPrompt,
    attachments,
    addAttachment,
    isSending,
    submitGeneration,
    settings,
    addToast,
  } = useAppStore();

  const { hapticImpact, hapticNotification } = useTelegram();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showAttachmentMenu, setShowAttachmentMenu] = useState(false);

  // Check if send is enabled (has prompt text or attachments)
  const canSend = prompt.trim().length > 0 || attachments.length > 0;

  // Handle file selection with validation
  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files) return;

      let currentCount = attachments.length;

      Array.from(files).forEach((file) => {
        // Check attachment limit
        if (currentCount >= 3) {
          addToast({ message: "Maksimal 3 ta rasm qo'shish mumkin", type: 'error' });
          hapticNotification('warning');
          return;
        }

        // Validate file
        const validation = validateImageFile(file);
        if (!validation.valid) {
          addToast({ message: validation.error!, type: 'error' });
          hapticNotification('error');
          return;
        }

        // Create Object URL and add attachment
        const url = URL.createObjectURL(file);
        addAttachment({
          id: crypto.randomUUID(),
          url,
          file,
        });
        currentCount++;
      });

      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      setShowAttachmentMenu(false);
    },
    [addAttachment, attachments.length, addToast, hapticNotification]
  );

  // Handle send
  const handleSend = useCallback(async () => {
    if (!canSend || isSending) return;

    hapticImpact('medium');
    await submitGeneration();

    // Focus textarea after sending
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 100);
  }, [canSend, isSending, hapticImpact, submitGeneration]);

  // Handle key press (Enter to send on desktop)
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  // Auto-resize textarea
  const handleInput = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const textarea = e.target;
    setPrompt(textarea.value);

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    // Set to scrollHeight, max 120px
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
  }, [setPrompt]);

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-t from-dark-500 via-dark-500/95 to-transparent pt-8 pb-safe">
      <div className="max-w-[520px] mx-auto px-4 pb-4">
        {/* Attachment chips row */}
        <AnimatePresence>
          {attachments.length > 0 && <AttachmentChips />}
        </AnimatePresence>

        {/* Credits indicator */}
        <div className="flex items-center justify-end gap-1.5 mb-2 text-xs text-white/40">
          <CreditIcon size={14} className="text-white/30" />
          <span>{settings.creditsPerImage} / image</span>
        </div>

        {/* Main composer row */}
        <div className="flex items-end gap-2">
          {/* Add attachment button */}
          <div className="relative">
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => setShowAttachmentMenu(!showAttachmentMenu)}
              className="flex items-center justify-center w-11 h-11 rounded-full bg-surface border border-white/5 hover:bg-surface-light transition-colors"
              aria-label="Add attachment"
            >
              <PlusIcon size={22} className="text-white/60" />
            </motion.button>

            {/* Attachment menu popup */}
            <AnimatePresence>
              {showAttachmentMenu && (
                <motion.div
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute bottom-14 left-0 w-48 bg-surface rounded-xl border border-white/10 shadow-soft overflow-hidden"
                >
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-3 w-full px-4 py-3 text-sm text-white/80 hover:bg-white/5 transition-colors"
                  >
                    <ImageIcon size={18} className="text-white/50" />
                    <span>Choose from device</span>
                  </button>
                  <button
                    onClick={() => {
                      // Camera API (if available)
                      fileInputRef.current?.click();
                    }}
                    className="flex items-center gap-3 w-full px-4 py-3 text-sm text-white/80 hover:bg-white/5 transition-colors"
                  >
                    <CameraIcon size={18} className="text-white/50" />
                    <span>Take a photo</span>
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept={ALLOWED_EXTENSIONS}
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {/* Text input container */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={prompt}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Describe the image you're imagining"
              rows={1}
              className="w-full px-4 py-3 pr-12 text-sm text-white/90 placeholder-white/30 bg-surface border border-white/5 rounded-2xl resize-none outline-none focus:border-white/10 transition-colors"
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
          </div>

          {/* Send button */}
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={handleSend}
            disabled={!canSend || isSending}
            className={`flex items-center justify-center w-11 h-11 rounded-full transition-all duration-200 ${
              canSend
                ? 'bg-banana-500 hover:bg-banana-400 shadow-glow'
                : 'bg-surface border border-white/5'
            }`}
            aria-label="Send"
          >
            {isSending ? (
              <SpinnerIcon size={20} className={canSend ? 'text-dark-500' : 'text-white/30'} />
            ) : (
              <SendIcon
                size={20}
                className={canSend ? 'text-dark-500' : 'text-white/30'}
              />
            )}
          </motion.button>
        </div>
      </div>

      {/* Backdrop to close attachment menu */}
      <AnimatePresence>
        {showAttachmentMenu && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowAttachmentMenu(false)}
            className="fixed inset-0 z-[-1]"
          />
        )}
      </AnimatePresence>
    </div>
  );
});
