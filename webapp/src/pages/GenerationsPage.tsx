import { useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  HeaderBar,
  GenerationFeed,
  ComposerBar,
  FullscreenViewer,
  BottomSheetMenu,
  ToastContainer,
} from '../components';
import { useAppStore } from '../store';
import { useTelegram } from '../hooks/useTelegram';
import { logger } from '../services/logger';

/**
 * GenerationsPage - Main page component for the AI image generation webapp
 * Combines feed, composer, viewer, and other UI elements
 */
export function GenerationsPage() {
  const { initialize, isLoading, stopPolling } = useAppStore();
  const { isReady, user } = useTelegram();

  // Log page mount
  useEffect(() => {
    logger.ui.info('GenerationsPage mounted');
    return () => {
      logger.ui.debug('GenerationsPage unmounted');
      // Stop polling on unmount
      stopPolling();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    // stopPolling is a stable Zustand store action
  }, []);

  // Initialize store with user's telegram ID
  useEffect(() => {
    if (isReady && user?.id) {
      logger.generation.info('Initializing store', { userId: user.id });
      initialize(user.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    // initialize is a stable Zustand store action
  }, [isReady, user?.id]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col h-screen bg-dark-500 max-w-[520px] mx-auto relative"
    >
      {/* Subtle background gradient */}
      <div className="fixed inset-0 bg-gradient-to-b from-dark-400/50 via-dark-500 to-dark-600 pointer-events-none" />

      {/* Header */}
      <HeaderBar />

      {/* Main content area - feed */}
      <main className="flex-1 relative z-10 overflow-hidden">
        <GenerationFeed />
      </main>

      {/* Bottom composer */}
      <ComposerBar />

      {/* Overlays */}
      <FullscreenViewer />
      <BottomSheetMenu />
      <ToastContainer />

      {/* Loading overlay for initial load */}
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[300] flex items-center justify-center bg-dark-500"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
            className="w-12 h-12 border-3 border-banana-500/20 border-t-banana-500 rounded-full"
          />
        </motion.div>
      )}
    </motion.div>
  );
}
