import { memo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CopyIcon, DownloadIcon, RefreshIcon, TrashIcon } from './Icons';
import { useAppStore } from '../store';
import { useTelegram } from '../hooks/useTelegram';

/**
 * BottomSheetMenu component - slide-up action menu for generation cards
 * Actions: Copy prompt, Download, Regenerate, Delete
 */
export const BottomSheetMenu = memo(function BottomSheetMenu() {
  const { menuGeneration, setMenuGeneration, deleteGeneration, addToast } = useAppStore();
  const { hapticImpact } = useTelegram();

  const handleClose = useCallback(() => {
    setMenuGeneration(null);
  }, [setMenuGeneration]);

  const handleCopyPrompt = useCallback(async () => {
    if (!menuGeneration?.prompt) return;

    try {
      await navigator.clipboard.writeText(menuGeneration.prompt);
      hapticImpact('light');
      addToast({ message: 'Prompt copied to clipboard', type: 'success' });
    } catch {
      addToast({ message: 'Failed to copy prompt', type: 'error' });
    }
    handleClose();
  }, [menuGeneration, hapticImpact, addToast, handleClose]);

  const handleDownload = useCallback(async () => {
    if (!menuGeneration?.resultUrl) return;

    try {
      hapticImpact('light');

      // Create a temporary link to download the image
      const response = await fetch(menuGeneration.resultUrl);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = url;
      link.download = `bananapics-${menuGeneration.id}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      addToast({ message: 'Image downloaded', type: 'success' });
    } catch {
      addToast({ message: 'Failed to download image', type: 'error' });
    }
    handleClose();
  }, [menuGeneration, hapticImpact, addToast, handleClose]);

  const handleRegenerate = useCallback(() => {
    if (!menuGeneration) return;

    hapticImpact('medium');
    // Copy prompt to composer for regeneration
    useAppStore.getState().setPrompt(menuGeneration.prompt);
    addToast({ message: 'Prompt copied to composer', type: 'info' });
    handleClose();
  }, [menuGeneration, hapticImpact, addToast, handleClose]);

  const handleDelete = useCallback(() => {
    if (!menuGeneration) return;

    hapticImpact('medium');
    deleteGeneration(menuGeneration.id);
  }, [menuGeneration, hapticImpact, deleteGeneration]);

  const actions = [
    {
      id: 'copy',
      label: 'Copy prompt',
      icon: <CopyIcon size={20} />,
      onClick: handleCopyPrompt,
      disabled: !menuGeneration?.prompt,
    },
    {
      id: 'download',
      label: 'Download image',
      icon: <DownloadIcon size={20} />,
      onClick: handleDownload,
      disabled: !menuGeneration?.resultUrl,
    },
    {
      id: 'regenerate',
      label: 'Regenerate',
      icon: <RefreshIcon size={20} />,
      onClick: handleRegenerate,
    },
    {
      id: 'delete',
      label: 'Delete',
      icon: <TrashIcon size={20} />,
      onClick: handleDelete,
      destructive: true,
    },
  ];

  return (
    <AnimatePresence>
      {menuGeneration && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={handleClose}
            className="fixed inset-0 z-[90] bg-black/60 backdrop-blur-sm"
          />

          {/* Sheet */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 400 }}
            className="fixed bottom-0 left-0 right-0 z-[95] bg-surface rounded-t-3xl border-t border-white/5 pb-safe"
          >
            {/* Handle */}
            <div className="flex justify-center py-3">
              <div className="w-10 h-1 rounded-full bg-white/20" />
            </div>

            {/* Actions list */}
            <div className="px-4 pb-6">
              {actions.map((action) => (
                <motion.button
                  key={action.id}
                  whileTap={{ scale: 0.98 }}
                  onClick={action.onClick}
                  disabled={action.disabled}
                  className={`flex items-center gap-4 w-full px-4 py-4 rounded-xl transition-colors ${
                    action.disabled
                      ? 'opacity-40 cursor-not-allowed'
                      : action.destructive
                      ? 'text-red-400 hover:bg-red-500/10'
                      : 'text-white/80 hover:bg-white/5'
                  }`}
                >
                  <span className={action.destructive ? 'text-red-400' : 'text-white/50'}>
                    {action.icon}
                  </span>
                  <span className="text-base font-medium">{action.label}</span>
                </motion.button>
              ))}
            </div>

            {/* Cancel button */}
            <div className="px-4 pb-4">
              <motion.button
                whileTap={{ scale: 0.98 }}
                onClick={handleClose}
                className="w-full py-4 text-base font-medium text-white/60 bg-dark-300 rounded-xl hover:bg-dark-200 transition-colors"
              >
                Cancel
              </motion.button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
});
