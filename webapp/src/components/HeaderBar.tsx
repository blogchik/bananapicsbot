import { memo } from 'react';
import { motion } from 'framer-motion';
import { BananaIcon, UserIcon } from './Icons';
import { useAppStore } from '../store';

/**
 * HeaderBar component with mode pill and profile button
 * Matches the dark, minimal design from screenshots
 */
export const HeaderBar = memo(function HeaderBar() {
  const settings = useAppStore((s) => s.settings);

  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="sticky top-0 z-40 flex items-center justify-between px-4 py-3 bg-dark-500/80 backdrop-blur-xl"
    >
      {/* Mode Pill - shows model, ratio, quality */}
      <motion.div
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, duration: 0.2 }}
        className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-surface border border-white/5 shadow-soft"
      >
        {/* Logo icon */}
        <BananaIcon size={20} className="text-banana-400/80" />

        {/* Mode info text */}
        <div className="flex items-center gap-1.5 text-sm">
          <span className="text-white/90 font-medium">{settings.model}</span>
          <span className="text-white/30">|</span>
          <span className="text-white/60">{settings.ratio}</span>
          <span className="text-white/30">|</span>
          <span className="text-white/60">{settings.quality}</span>
        </div>
      </motion.div>

      {/* Profile/Settings button */}
      <motion.button
        whileTap={{ scale: 0.95 }}
        className="flex items-center justify-center w-11 h-11 rounded-full bg-surface border border-white/5 transition-colors hover:bg-surface-light active:bg-surface-lighter"
        aria-label="Profile settings"
      >
        <UserIcon size={20} className="text-white/60" />
      </motion.button>
    </motion.header>
  );
});
