import { memo, useCallback, useRef, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { GenerationCard, SkeletonCard } from './GenerationCard';
import { EmptyState } from './EmptyState';
import { useAppStore } from '../store';

/**
 * GenerationFeed component - Instagram-like vertical scroll feed
 * Handles loading, empty, and populated states
 * Feed shows oldest at top, newest at bottom (reversed chronological)
 */
export const GenerationFeed = memo(function GenerationFeed() {
  const {
    generations,
    isLoading,
    setSelectedGeneration,
    setMenuGeneration,
  } = useAppStore();

  const scrollContainerRef = useRef<HTMLDivElement>(null);

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

  // Auto-scroll to bottom (latest generation) when generations load or update
  useEffect(() => {
    if (!isLoading && generations.length > 0 && scrollContainerRef.current) {
      // Use setTimeout to ensure DOM is ready
      setTimeout(() => {
        scrollContainerRef.current?.scrollTo({
          top: scrollContainerRef.current.scrollHeight,
          behavior: 'smooth',
        });
      }, 100);
    }
  }, [generations.length, isLoading]);

  // Loading state - show skeleton cards
  if (isLoading) {
    return (
      <div ref={scrollContainerRef} className="h-full overflow-y-auto pt-20 pb-24">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} index={i} />
        ))}
      </div>
    );
  }

  // Empty state - no generations yet
  if (generations.length === 0) {
    return (
      <div className="h-full flex items-center justify-center pt-20 pb-24">
        <EmptyState />
      </div>
    );
  }

  // Populated feed - reverse chronological (oldest at top, newest at bottom)
  const reversedGenerations = [...generations].reverse();

  return (
    <div ref={scrollContainerRef} className="h-full overflow-y-auto pt-20 pb-24 scroll-smooth">
      <AnimatePresence mode="popLayout">
        {reversedGenerations.map((generation, index) => (
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
