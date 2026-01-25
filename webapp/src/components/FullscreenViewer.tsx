import { memo, useCallback, useState } from 'react';
import { motion, AnimatePresence, useDragControls, PanInfo } from 'framer-motion';
import { CloseIcon } from './Icons';
import { useAppStore } from '../store';

/**
 * FullscreenViewer component for viewing images in full screen
 * Supports swipe down to close on mobile
 */
export const FullscreenViewer = memo(function FullscreenViewer() {
  const { selectedGeneration, setSelectedGeneration } = useAppStore();
  const dragControls = useDragControls();
  const [dragY, setDragY] = useState(0);

  const handleClose = useCallback(() => {
    setSelectedGeneration(null);
  }, [setSelectedGeneration]);

  const handleDrag = useCallback((_: unknown, info: PanInfo) => {
    setDragY(info.offset.y);
  }, []);

  const handleDragEnd = useCallback(
    (_: unknown, info: PanInfo) => {
      // Close if dragged down more than 100px or with velocity
      if (info.offset.y > 100 || info.velocity.y > 500) {
        handleClose();
      }
      setDragY(0);
    },
    [handleClose]
  );

  // Calculate backdrop opacity based on drag
  const backdropOpacity = Math.max(0.2, 1 - Math.abs(dragY) / 400);

  return (
    <AnimatePresence>
      {selectedGeneration?.resultUrl && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[100] flex items-center justify-center"
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-black"
            style={{ opacity: backdropOpacity }}
            onClick={handleClose}
          />

          {/* Close button */}
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ delay: 0.1 }}
            onClick={handleClose}
            className="absolute top-4 right-4 pt-safe pr-safe z-10 w-10 h-10 flex items-center justify-center rounded-full bg-white/10 backdrop-blur-md"
            aria-label="Close viewer"
          >
            <CloseIcon size={20} className="text-white" />
          </motion.button>

          {/* Image container - draggable */}
          <motion.div
            drag="y"
            dragControls={dragControls}
            dragConstraints={{ top: 0, bottom: 0 }}
            dragElastic={0.8}
            onDrag={handleDrag}
            onDragEnd={handleDragEnd}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="relative max-w-full max-h-full p-4 cursor-grab active:cursor-grabbing"
          >
            <img
              src={selectedGeneration.resultUrl}
              alt={selectedGeneration.prompt || 'Generated image'}
              className="max-w-full max-h-[85vh] object-contain rounded-lg select-none"
              draggable={false}
            />

            {/* Prompt overlay at bottom */}
            {selectedGeneration.prompt && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="absolute bottom-8 left-8 right-8 p-4 bg-black/60 backdrop-blur-md rounded-xl"
              >
                <p className="text-sm text-white/80 line-clamp-3">
                  {selectedGeneration.prompt}
                </p>
              </motion.div>
            )}
          </motion.div>

          {/* Swipe hint */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            transition={{ delay: 0.5 }}
            className="absolute bottom-8 left-1/2 -translate-x-1/2 text-xs text-white/40"
          >
            Swipe down to close
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
});
