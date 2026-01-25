import { memo, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import { GenerationCard, SkeletonCard } from './GenerationCard';
import { EmptyState } from './EmptyState';
import { useAppStore } from '../store';

/**
 * GenerationFeed component - Instagram-like vertical scroll feed
 * Handles loading, empty, and populated states
 */
export const GenerationFeed = memo(function GenerationFeed() {
  const {
    generations,
    isLoading,
    setSelectedGeneration,
    setMenuGeneration,
  } = useAppStore();

  const handleImageClick = useCallback(
    (generation: typeof generations[0]) => {
      if (generation.status === 'done' && generation.resultUrl) {
        setSelectedGeneration(generation);
      }
    },
    [setSelectedGeneration]
  );

  const handleMenuClick = useCallback(
    (generation: typeof generations[0]) => {
      setMenuGeneration(generation);
    },
    [setMenuGeneration]
  );

  // Loading state - show skeleton cards
  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto pt-2 pb-40">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} index={i} />
        ))}
      </div>
    );
  }

  // Empty state - no generations yet
  if (generations.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center pb-40">
        <EmptyState />
      </div>
    );
  }

  // Populated feed
  return (
    <div className="flex-1 overflow-y-auto pt-2 pb-40 scroll-smooth">
      <AnimatePresence mode="popLayout">
        {generations.map((generation, index) => (
          <GenerationCard
            key={generation.id}
            generation={generation}
            index={index}
            onImageClick={() => handleImageClick(generation)}
            onMenuClick={() => handleMenuClick(generation)}
          />
        ))}
      </AnimatePresence>
    </div>
  );
});
