import { memo, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PlusIcon, SendIcon, SpinnerIcon, CreditIcon } from './Icons';
import { AttachmentChips } from './AttachmentChips';
import { useAppStore } from '../store';
import { useTelegram } from '../hooks/useTelegram';
import { useTranslation } from '../hooks/useTranslation';
import { TranslationKey } from '../locales';

// File validation constants
const ALLOWED_EXTENSIONS = '.jpg,.jpeg,.png,.webp,.gif,.bmp,.tiff,.tif';

const MAX_FILE_SIZE_MB = 20;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024; // 20MB in bytes

// Magic bytes signatures for image formats
// Used to validate actual file content, preventing MIME type spoofing
const IMAGE_SIGNATURES: { format: string; signatures: number[][] }[] = [
  { format: 'jpeg', signatures: [[0xFF, 0xD8, 0xFF]] },
  { format: 'png', signatures: [[0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]] },
  { format: 'gif', signatures: [[0x47, 0x49, 0x46, 0x38, 0x37, 0x61], [0x47, 0x49, 0x46, 0x38, 0x39, 0x61]] }, // GIF87a and GIF89a
  { format: 'bmp', signatures: [[0x42, 0x4D]] }, // "BM"
  { format: 'tiff', signatures: [[0x49, 0x49, 0x2A, 0x00], [0x4D, 0x4D, 0x00, 0x2A]] }, // Little-endian and big-endian
];

// WebP has a special structure: RIFF....WEBP
const WEBP_RIFF = [0x52, 0x49, 0x46, 0x46]; // "RIFF"
const WEBP_MARKER = [0x57, 0x45, 0x42, 0x50]; // "WEBP" at offset 8

// Check if bytes match a signature
function matchesSignature(bytes: Uint8Array, signature: number[]): boolean {
  if (bytes.length < signature.length) return false;
  return signature.every((byte, index) => bytes[index] === byte);
}

// Validate file signature using magic bytes
async function validateFileSignature(file: File): Promise<{ valid: boolean; format?: string }> {
  try {
    // Read the first 12 bytes (enough for all signatures including WebP)
    const buffer = await file.slice(0, 12).arrayBuffer();
    const bytes = new Uint8Array(buffer);

    // Check WebP separately (RIFF + WEBP at offset 8)
    if (matchesSignature(bytes, WEBP_RIFF) && bytes.length >= 12) {
      const webpMarkerBytes = bytes.slice(8, 12);
      if (matchesSignature(webpMarkerBytes, WEBP_MARKER)) {
        return { valid: true, format: 'webp' };
      }
    }

    // Check other image signatures
    for (const { format, signatures } of IMAGE_SIGNATURES) {
      for (const signature of signatures) {
        if (matchesSignature(bytes, signature)) {
          return { valid: true, format };
        }
      }
    }

    return { valid: false };
  } catch {
    return { valid: false };
  }
}

// Validate file type (via magic bytes) and size
async function validateImageFile(
  file: File,
  t: (key: TranslationKey, params?: Record<string, string | number>) => string
): Promise<{ valid: boolean; error?: string }> {
  // Check file size first (quick check)
  if (file.size > MAX_FILE_SIZE_BYTES) {
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
    return {
      valid: false,
      error: t(TranslationKey.FILE_SIZE_TOO_LARGE, {
        fileSizeMB,
        maxSizeMB: MAX_FILE_SIZE_MB,
      }),
    };
  }

  // Validate file signature using magic bytes (prevents MIME type spoofing)
  const signatureCheck = await validateFileSignature(file);
  if (!signatureCheck.valid) {
    return {
      valid: false,
      error: t(TranslationKey.FILE_TYPE_NOT_SUPPORTED),
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
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Check if send is enabled (has prompt text or attachments)
  const canSend = prompt.trim().length > 0 || attachments.length > 0;

  // Handle file selection with validation
  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files) return;

      let currentCount = attachments.length;

      for (const file of Array.from(files)) {
        // Check attachment limit
        if (currentCount >= 3) {
          addToast({
            message: t(TranslationKey.MAX_ATTACHMENTS_REACHED),
            type: 'error',
          });
          hapticNotification('warning');
          break;
        }

        // Validate file (includes magic bytes check to prevent MIME spoofing)
        const validation = await validateImageFile(file, t);
        if (!validation.valid) {
          addToast({ message: validation.error!, type: 'error' });
          hapticNotification('error');
          continue;
        }

        // Create Object URL and add attachment
        const url = URL.createObjectURL(file);
        addAttachment({
          id: crypto.randomUUID(),
          url,
          file,
        });
        currentCount++;
      }

      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
    [addAttachment, attachments.length, addToast, hapticNotification, t]
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
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-t from-dark-500 via-dark-500/98 to-transparent pt-6 pb-safe">
      <div className="max-w-[520px] mx-auto px-4 pb-3">
        {/* Attachment chips row */}
        <AnimatePresence>
          {attachments.length > 0 && (
            <div className="mb-3">
              <AttachmentChips />
            </div>
          )}
        </AnimatePresence>

        {/* Main composer row with input */}
        <div className="relative">
          {/* Credits indicator - absolute positioned in top right */}
          <div className="absolute -top-7 right-0 flex items-center gap-1.5 text-xs text-white/40">
            <CreditIcon size={12} className="text-white/30" />
            <span>{settings.creditsPerImage} / image</span>
          </div>

          {/* Composer input row */}
          <div className="flex items-center gap-2.5 bg-surface/60 backdrop-blur-sm rounded-full border border-white/5 px-1.5 py-1.5">
            {/* Add attachment button - hide when 3 attachments */}
            <AnimatePresence mode="wait">
              {attachments.length < 3 && (
                <motion.div
                  key="add-button"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                >
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center justify-center w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 transition-colors"
                    aria-label={t(TranslationKey.ARIA_ADD_ATTACHMENT)}
                  >
                    <PlusIcon size={20} className="text-white/60" />
                  </motion.button>

                  {/* Hidden file input */}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={ALLOWED_EXTENSIONS}
                    multiple
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Text input container */}
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={prompt}
                onChange={handleInput}
                onKeyDown={handleKeyDown}
                placeholder="Describe the image you're imagining"
                rows={1}
                className="w-full px-3 py-2.5 text-sm text-white/90 placeholder-white/40 bg-transparent resize-none outline-none"
                style={{ minHeight: '40px', maxHeight: '120px' }}
              />
            </div>

            {/* Send button */}
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={handleSend}
              disabled={!canSend || isSending}
              className={`flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full transition-all duration-200 ${
                canSend
                  ? 'bg-white/95 hover:bg-white shadow-lg'
                  : 'bg-white/5'
              }`}
              aria-label={t(TranslationKey.ARIA_SEND)}
            >
              {isSending ? (
                <SpinnerIcon size={18} className={canSend ? 'text-dark-500' : 'text-white/30'} />
              ) : (
                <SendIcon
                  size={18}
                  className={canSend ? 'text-dark-500' : 'text-white/30'}
                />
              )}
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  );
});
