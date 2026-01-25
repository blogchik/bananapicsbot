import { memo, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BananaIcon, HeartIcon, HeartFilledIcon, MoreIcon, RefreshIcon } from './Icons';
import { useAppStore } from '../store';
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
  const { toggleLike, retryGeneration } = useAppStore();
  const [imageLoaded, setImageLoaded] = useState(false);
  const [isLikeAnimating, setIsLikeAnimating] = useState(false);

  const handleLike = useCallback(() => {
    setIsLikeAnimating(true);
    toggleLike(generation.id);
    setTimeout(() => setIsLikeAnimating(false), 300);
  }, [generation.id, toggleLike]);

  const handleRetry = useCallback(() => {
    retryGeneration(generation.id);
  }, [generation.id, retryGeneration]);

  const isGenerating = generation.status === 'generating';
  const isError = generation.status === 'error';
  const isDone = generation.status === 'done';

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="mb-4"
    >
      {/* Prompt text preview */}
      {generation.prompt && (
        <p className="px-4 mb-3 text-sm text-white/80 line-clamp-2 leading-relaxed">
          {generation.prompt}
        </p>
      )}

      {/* Image container */}
      <div className="relative mx-4 rounded-2xl overflow-hidden bg-surface">
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
            className={`w-full aspect-[4/3] object-cover cursor-pointer transition-opacity duration-300 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
          />
        )}

        {/* Placeholder aspect ratio for loading states */}
        {(isGenerating || isError || !generation.resultUrl) && (
          <div className="w-full aspect-[4/3]" />
        )}

        {/* Watermark overlay (visible on hover on desktop) */}
        {isDone && imageLoaded && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20">
            <span className="text-4xl font-light tracking-[0.3em] text-white/30 select-none">
              BananaPics
            </span>
          </div>
        )}
      </div>

      {/* Metadata row */}
      <div className="flex items-center justify-between px-4 mt-3">
        <div className="flex items-center gap-2 text-xs text-white/40">
          <BananaIcon size={16} className="text-white/30" />
          <span>{generation.model}</span>
          <span className="text-white/20">|</span>
          <span>{generation.ratio}</span>
          <span className="text-white/20">|</span>
          <span>{generation.quality}</span>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1">
          {/* Like button */}
          <motion.button
            whileTap={{ scale: 0.85 }}
            onClick={handleLike}
            className="p-2 rounded-full hover:bg-white/5 transition-colors"
            aria-label={generation.liked ? 'Unlike' : 'Like'}
          >
            <motion.div animate={isLikeAnimating ? { scale: [1, 1.3, 1] } : {}}>
              {generation.liked ? (
                <HeartFilledIcon size={20} className="text-red-500" />
              ) : (
                <HeartIcon size={20} className="text-white/40" />
              )}
            </motion.div>
          </motion.button>

          {/* More/Menu button */}
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={onMenuClick}
            className="p-2 rounded-full hover:bg-white/5 transition-colors"
            aria-label="More options"
          >
            <MoreIcon size={20} className="text-white/40" />
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
      className="mb-4"
    >
      {/* Skeleton prompt */}
      <div className="px-4 mb-3 space-y-2">
        <div className="h-3 w-3/4 bg-surface rounded animate-pulse" />
        <div className="h-3 w-1/2 bg-surface rounded animate-pulse" />
      </div>

      {/* Skeleton image */}
      <div className="mx-4 rounded-2xl overflow-hidden">
        <div className="w-full aspect-[4/3] bg-gradient-to-r from-surface via-surface-light to-surface bg-[length:200%_100%] animate-shimmer" />
      </div>

      {/* Skeleton metadata */}
      <div className="flex items-center justify-between px-4 mt-3">
        <div className="h-3 w-32 bg-surface rounded animate-pulse" />
        <div className="flex gap-2">
          <div className="w-8 h-8 bg-surface rounded-full animate-pulse" />
          <div className="w-8 h-8 bg-surface rounded-full animate-pulse" />
        </div>
      </div>
    </motion.div>
  );
});
