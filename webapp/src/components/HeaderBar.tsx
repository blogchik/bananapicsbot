import { memo } from 'react';
import { motion } from 'framer-motion';
import { BananaIcon, UserIcon } from './Icons';
import { useAppStore } from '../store';
import { useTranslation } from '../hooks/useTranslation';
import { TranslationKey } from '../locales';

/**
 * HeaderBar component with mode pill and profile button
 * Matches the dark, minimal design from screenshots
 *
 * Structure:
 * - Outer container: handles safe area padding (for Telegram header/status bar)
 * - Inner container: handles content layout and styling
 */
export const HeaderBar = memo(function HeaderBar() {
  const settings = useAppStore((s) => s.settings);
  const { t } = useTranslation();

  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="sticky top-0 z-40 bg-dark-500/80 backdrop-blur-xl"
    >
      {/* Safe area spacer - accounts for Telegram UI and device notches */}
      <div className="pt-tg-safe" />

      {/* Header content - separated from safe area for cleaner layout */}
      <div className="flex items-center justify-between px-4 py-3">
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
          aria-label={t(TranslationKey.ARIA_PROFILE_SETTINGS)}
        >
          <UserIcon size={20} className="text-white/60" />
        </motion.button>
      </div>
    </motion.header>
  );
});
