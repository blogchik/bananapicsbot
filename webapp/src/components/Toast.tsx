import { memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../store';

/**
 * Toast notification system
 * Shows temporary messages for success, error, and info states
 */
export const ToastContainer = memo(function ToastContainer() {
  const toasts = useAppStore((s) => s.toasts);

  return (
    <div
      className="fixed left-4 right-4 z-[200] flex flex-col items-center gap-2 pointer-events-none"
      style={{
        // Position below header: safe area + header content height + gap
        top: 'calc(var(--tg-safe-area-top, 72px) + var(--header-content-height, 56px) + 8px)',
      }}
    >
      <AnimatePresence mode="sync">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} />
        ))}
      </AnimatePresence>
    </div>
  );
});

interface ToastItemProps {
  toast: { id: string; message: string; type: 'success' | 'error' | 'info' };
}

const ToastItem = memo(function ToastItem({ toast }: ToastItemProps) {
  const removeToast = useAppStore((s) => s.removeToast);

  const bgColor = {
    success: 'bg-green-500/90',
    error: 'bg-red-500/90',
    info: 'bg-white/10',
  }[toast.type];

  const textColor = {
    success: 'text-white',
    error: 'text-white',
    info: 'text-white/90',
  }[toast.type];

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.9 }}
      transition={{ type: 'spring', damping: 20, stiffness: 300 }}
      onClick={() => removeToast(toast.id)}
      className={`px-4 py-3 rounded-xl ${bgColor} backdrop-blur-md shadow-soft pointer-events-auto cursor-pointer`}
    >
      <p className={`text-sm font-medium ${textColor}`}>{toast.message}</p>
    </motion.div>
  );
});
