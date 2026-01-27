import { memo, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BananaIcon, HeartIcon, HeartFilledIcon, MoreIcon, RefreshIcon, ChevronDownIcon, CopyIcon } from './Icons';
import { useAppStore } from '../store';
import { useTranslation } from '../hooks/useTranslation';
import { TranslationKey } from '../locales';
import type { GenerationItem } from '../types';

interface GenerationCardProps {
  generation: GenerationItem;
  index: number;
  onImageClick: () => void;
  onMenuClick: () => void;
}

/**
 * GenerationCard component displaying a single generation
 * Shows prompt, image, metadata, and action buttons
 */
export const GenerationCard = memo(function GenerationCard({
  generation,
  index,
  onImageClick,
  onMenuClick,
}: GenerationCardProps) {
  const { toggleLike, retryGeneration, addToast } = useAppStore();
  const { t } = useTranslation();
  const [imageLoaded, setImageLoaded] = useState(false);
  const [isLikeAnimating, setIsLikeAnimating] = useState(false);
  const [isPromptExpanded, setIsPromptExpanded] = useState(false);

  const handleLike = useCallback(() => {
    setIsLikeAnimating(true);
    toggleLike(generation.id);
    setTimeout(() => setIsLikeAnimating(false), 300);
  }, [generation.id, toggleLike]);

  const handleRetry = useCallback(() => {
    retryGeneration(generation.id);
  }, [generation.id, retryGeneration]);

  const handleCopyPrompt = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(generation.prompt);
      addToast({
        message: 'Prompt copied to clipboard',
        type: 'success',
        duration: 2000,
      });
    } catch (error) {
      addToast({
        message: 'Failed to copy prompt',
        type: 'error',
        duration: 2000,
      });
    }
  }, [generation.prompt, addToast]);

  const togglePromptExpanded = useCallback(() => {
    setIsPromptExpanded((prev) => !prev);
  }, []);

  const isGenerating = generation.status === 'generating';
  const isError = generation.status === 'error';
  const isDone = generation.status === 'done';

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="mb-6"
    >
      {/* Prompt text with expand/collapse and copy */}
      {generation.prompt && (
        <div className="px-4 mb-2">
          <div className="flex items-start gap-2">
            <p
              className={`flex-1 text-sm text-white/90 leading-[1.6] ${
                isPromptExpanded ? '' : 'line-clamp-2'
              }`}
            >
              {generation.prompt}
            </p>
            <div className="flex items-center gap-0.5 flex-shrink-0 mt-0.5">
              {/* Copy prompt button */}
              <motion.button
                whileTap={{ scale: 0.85 }}
                onClick={handleCopyPrompt}
                className="p-2 rounded-full hover:bg-white/10 active:bg-white/15 transition-colors"
                aria-label="Copy prompt"
              >
                <CopyIcon size={14} className="text-white/50 hover:text-white/70" />
              </motion.button>
              {/* Expand/collapse toggle */}
              <motion.button
                whileTap={{ scale: 0.85 }}
                onClick={togglePromptExpanded}
                className="p-2 rounded-full hover:bg-white/10 active:bg-white/15 transition-colors"
                aria-label={isPromptExpanded ? 'Show less' : 'Show more'}
              >
                <motion.div
                  animate={{ rotate: isPromptExpanded ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <ChevronDownIcon size={14} className="text-white/50 hover:text-white/70" />
                </motion.div>
              </motion.button>
            </div>
          </div>
        </div>
      )}

      {/* Image container */}
      <div className="relative mx-4 rounded-3xl overflow-hidden bg-surface shadow-lg">
        {/* Shimmer loading state */}
        <AnimatePresence>
          {(isGenerating || (!imageLoaded && isDone)) && (
            <motion.div
              initial={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-gradient-to-r from-surface via-surface-light to-surface bg-[length:200%_100%] animate-shimmer"
            />
          )}
        </AnimatePresence>

        {/* Generating indicator */}
        {isGenerating && (
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              className="w-8 h-8 border-2 border-banana-500/30 border-t-banana-500 rounded-full"
            />
          </div>
        )}

        {/* Error state */}
        {isError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-surface/90">
            <p className="text-sm text-red-400">{generation.errorMessage || 'Generation failed'}</p>
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={handleRetry}
              className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-white/10 rounded-full hover:bg-white/15 transition-colors"
            >
              <RefreshIcon size={16} />
              <span>Retry</span>
            </motion.button>
          </div>
        )}

        {/* Result image */}
        {isDone && generation.resultUrl && (
          <motion.img
            src={generation.resultUrl}
            alt={generation.prompt || 'Generated image'}
            loading="lazy"
            onLoad={() => setImageLoaded(true)}
            onClick={onImageClick}
            className={`w-full object-contain cursor-pointer transition-opacity duration-300 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
          />
        )}

        {/* Placeholder for loading states */}
        {(isGenerating || isError || !generation.resultUrl) && (
          <div className="w-full aspect-[4/3]" />
        )}

        {/* Watermark overlay */}
        {isDone && imageLoaded && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-10">
            <span className="text-3xl font-extralight tracking-[0.4em] text-white/40 select-none">
              BananaPics
            </span>
          </div>
        )}
      </div>

      {/* Metadata row */}
      <div className="flex items-center justify-between px-4 mt-2.5">
        <div className="flex items-center gap-2 text-xs text-white/50">
          <BananaIcon size={14} className="text-white/40" />
          <span>{generation.model}</span>
          <span className="text-white/25">•</span>
          <span>{generation.ratio}</span>
          <span className="text-white/25">•</span>
          <span>{generation.quality}</span>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-0.5">
          {/* Like button */}
          <motion.button
            whileTap={{ scale: 0.85 }}
            onClick={handleLike}
            className="p-2.5 rounded-full hover:bg-white/10 active:bg-white/15 transition-colors"
            aria-label={
              generation.liked
                ? t(TranslationKey.ARIA_UNLIKE)
                : t(TranslationKey.ARIA_LIKE)
            }
          >
            <motion.div animate={isLikeAnimating ? { scale: [1, 1.3, 1] } : {}}>
              {generation.liked ? (
                <HeartFilledIcon size={18} className="text-red-500" />
              ) : (
                <HeartIcon size={18} className="text-white/50" />
              )}
            </motion.div>
          </motion.button>

          {/* More/Menu button */}
          <motion.button
            whileTap={{ scale: 0.85 }}
            onClick={onMenuClick}
            className="p-2.5 rounded-full hover:bg-white/10 active:bg-white/15 transition-colors"
            aria-label={t(TranslationKey.ARIA_MORE_OPTIONS)}
          >
            <MoreIcon size={18} className="text-white/50" />
          </motion.button>
        </div>
      </div>
    </motion.article>
  );
});

/**
 * SkeletonCard for loading state
 */
export const SkeletonCard = memo(function SkeletonCard({ index }: { index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: index * 0.1 }}
      className="mb-6"
    >
      {/* Skeleton prompt */}
      <div className="px-4 mb-2 space-y-2">
        <div className="h-3.5 w-3/4 bg-surface rounded animate-pulse" />
        <div className="h-3.5 w-1/2 bg-surface rounded animate-pulse" />
      </div>

      {/* Skeleton image */}
      <div className="mx-4 rounded-3xl overflow-hidden shadow-lg">
        <div className="w-full aspect-[4/3] bg-gradient-to-r from-surface via-surface-light to-surface bg-[length:200%_100%] animate-shimmer" />
      </div>

      {/* Skeleton metadata */}
      <div className="flex items-center justify-between px-4 mt-2.5">
        <div className="h-3 w-32 bg-surface rounded animate-pulse" />
        <div className="flex gap-0.5">
          <div className="w-9 h-9 bg-surface rounded-full animate-pulse" />
          <div className="w-9 h-9 bg-surface rounded-full animate-pulse" />
        </div>
      </div>
    </motion.div>
  );
});
