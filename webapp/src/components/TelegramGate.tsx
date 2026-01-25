import { memo } from 'react';
import { motion } from 'framer-motion';

/**
 * Shield with lock icon - security illustration
 */
function ShieldLockIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 120 140"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Shield background */}
      <path
        d="M60 5L10 25V65C10 100 60 135 60 135C60 135 110 100 110 65V25L60 5Z"
        fill="url(#shieldGradient)"
        stroke="#2a2a3a"
        strokeWidth="2"
      />
      {/* Lock body */}
      <rect
        x="40"
        y="60"
        width="40"
        height="35"
        rx="4"
        fill="#1a1a24"
        stroke="#3a3a4a"
        strokeWidth="2"
      />
      {/* Lock shackle */}
      <path
        d="M48 60V50C48 43.3726 53.3726 38 60 38C66.6274 38 72 43.3726 72 50V60"
        stroke="#3a3a4a"
        strokeWidth="4"
        strokeLinecap="round"
        fill="none"
      />
      {/* Keyhole */}
      <circle cx="60" cy="74" r="5" fill="#3a3a4a" />
      <rect x="58" y="74" width="4" height="10" rx="2" fill="#3a3a4a" />

      <defs>
        <linearGradient id="shieldGradient" x1="60" y1="5" x2="60" y2="135" gradientUnits="userSpaceOnUse">
          <stop stopColor="#1e1e2a" />
          <stop offset="1" stopColor="#151520" />
        </linearGradient>
      </defs>
    </svg>
  );
}

/**
 * Sparkle/star decorative element
 */
function Sparkle({
  size = 8,
  delay = 0,
  className
}: {
  size?: number;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      initial={{ opacity: 0, scale: 0 }}
      animate={{
        opacity: [0, 1, 0],
        scale: [0.5, 1, 0.5],
      }}
      transition={{
        duration: 2,
        delay,
        repeat: Infinity,
        ease: "easeInOut"
      }}
    >
      <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" />
    </motion.svg>
  );
}

/**
 * TelegramGate component - blocks access when not opened via Telegram
 * Shows a security screen with shield/lock illustration and redirect link
 */
export const TelegramGate = memo(function TelegramGate() {
  const botUsername = 'BananPicsBot';
  const botLink = `https://t.me/${botUsername}`;

  return (
    <div className="fixed inset-0 z-[1000] bg-dark-500 flex flex-col items-center justify-center px-6">
      {/* Background subtle gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-dark-400/30 via-dark-500 to-dark-600/50 pointer-events-none" />

      {/* Content container */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative flex flex-col items-center"
      >
        {/* Sparkles around the shield */}
        <div className="absolute inset-0 pointer-events-none">
          <Sparkle size={6} delay={0} className="absolute top-0 right-4 text-white/20" />
          <Sparkle size={8} delay={0.3} className="absolute top-8 -right-2 text-white/15" />
          <Sparkle size={5} delay={0.6} className="absolute top-4 left-0 text-white/20" />
          <Sparkle size={7} delay={0.9} className="absolute bottom-16 right-0 text-white/15" />
          <Sparkle size={6} delay={1.2} className="absolute bottom-8 -left-4 text-white/20" />
          <Sparkle size={4} delay={1.5} className="absolute top-20 left-8 text-white/10" />
        </div>

        {/* Shield with lock illustration */}
        <motion.div
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{
            type: "spring",
            stiffness: 200,
            damping: 15,
            delay: 0.1
          }}
          className="w-32 h-36 mb-8"
        >
          <ShieldLockIcon className="w-full h-full" />
        </motion.div>

        {/* Message text */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-white/50 text-base text-center"
        >
          Use{' '}
          <a
            href={botLink}
            target="_blank"
            rel="noopener noreferrer"
            className="text-white/70 hover:text-white/90 transition-colors font-medium"
          >
            @{botUsername}
          </a>
          {' '}to launch app.
        </motion.p>
      </motion.div>
    </div>
  );
});
