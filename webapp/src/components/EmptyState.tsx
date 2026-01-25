import { memo } from 'react';
import { motion } from 'framer-motion';

/**
 * EmptyState component shown when there are no generations
 * Features a folder illustration with floating media icons
 */
export const EmptyState = memo(function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center justify-center py-20 px-4"
    >
      {/* Floating illustration */}
      <div className="relative w-64 h-48 mb-6">
        {/* Folder base */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="absolute inset-x-8 bottom-0"
        >
          <svg viewBox="0 0 200 120" fill="none" className="w-full h-auto">
            {/* Folder back */}
            <path
              d="M10 30C10 25 14 20 20 20H70L85 30H180C186 30 190 35 190 40V110C190 115 186 120 180 120H20C14 120 10 115 10 110V30Z"
              fill="#2A2A2A"
              stroke="#3A3A3A"
              strokeWidth="1"
            />
            {/* Folder front tab */}
            <path
              d="M10 40C10 35 14 30 20 30H60L75 20H85L100 30H180C186 30 190 35 190 40V50H10V40Z"
              fill="#333333"
              stroke="#3A3A3A"
              strokeWidth="1"
            />
            {/* Papers inside */}
            <rect x="25" y="50" width="50" height="35" rx="3" fill="#3A3A3A" />
            <rect x="30" y="55" width="40" height="3" rx="1" fill="#4A4A4A" />
            <rect x="30" y="62" width="30" height="3" rx="1" fill="#4A4A4A" />
            <rect x="30" y="69" width="35" height="3" rx="1" fill="#4A4A4A" />
          </svg>
        </motion.div>

        {/* Floating elements */}
        {/* Music note */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 0.5 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="absolute top-4 left-8"
        >
          <motion.div animate={{ y: [-2, 2, -2] }} transition={{ duration: 3, repeat: Infinity }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path
                d="M9 18V5l12-2v13M9 18c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3zm12-2c0 1.66-1.34 3-3 3s-3-1.34-3-3 1.34-3 3-3 3 1.34 3 3z"
                stroke="#555"
                strokeWidth="1.5"
                fill="none"
              />
            </svg>
          </motion.div>
        </motion.div>

        {/* Plus sign */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 0.4 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="absolute top-12 left-20"
        >
          <motion.div
            animate={{ y: [-3, 3, -3], rotate: [0, 10, 0] }}
            transition={{ duration: 4, repeat: Infinity, delay: 0.5 }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2v12M2 8h12" stroke="#555" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </motion.div>
        </motion.div>

        {/* Image/photo icon */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 0.5 }}
          transition={{ delay: 0.6, duration: 0.5 }}
          className="absolute top-2 left-28"
        >
          <motion.div animate={{ y: [-2, 4, -2] }} transition={{ duration: 3.5, repeat: Infinity }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="18" height="18" rx="2" stroke="#555" strokeWidth="1.5" />
              <circle cx="8" cy="8" r="1.5" fill="#555" />
              <path d="M21 15l-5-5L5 21" stroke="#555" strokeWidth="1.5" />
            </svg>
          </motion.div>
        </motion.div>

        {/* Video/film icon */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 0.5 }}
          transition={{ delay: 0.7, duration: 0.5 }}
          className="absolute top-0 right-12"
        >
          <motion.div
            animate={{ y: [-4, 2, -4], rotate: [0, -5, 0] }}
            transition={{ duration: 4, repeat: Infinity, delay: 1 }}
          >
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <rect x="2" y="4" width="20" height="16" rx="2" stroke="#555" strokeWidth="1.5" />
              <path d="M6 4v16M18 4v16M2 9h4M18 9h4M2 15h4M18 15h4" stroke="#555" strokeWidth="1.5" />
            </svg>
          </motion.div>
        </motion.div>

        {/* Play button */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 0.4 }}
          transition={{ delay: 0.8, duration: 0.5 }}
          className="absolute top-6 right-4"
        >
          <motion.div animate={{ y: [-2, 3, -2] }} transition={{ duration: 3, repeat: Infinity, delay: 0.3 }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <polygon points="5,3 19,12 5,21" fill="#555" />
            </svg>
          </motion.div>
        </motion.div>

        {/* Small dot decorations */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1, opacity: 0.3 }}
          transition={{ delay: 0.9, duration: 0.3 }}
          className="absolute bottom-20 left-4 w-2 h-2 rounded-full bg-white/20"
        />
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1, opacity: 0.3 }}
          transition={{ delay: 1, duration: 0.3 }}
          className="absolute bottom-24 right-8 w-1.5 h-1.5 rounded-full bg-white/20"
        />
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1, opacity: 0.3 }}
          transition={{ delay: 1.1, duration: 0.3 }}
          className="absolute top-20 left-2 w-1 h-1 rounded-full bg-white/20"
        />
      </div>

      {/* Helper text */}
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.4 }}
        className="text-white/40 text-sm text-center max-w-[200px]"
      >
        Your generations will appear here
      </motion.p>
    </motion.div>
  );
});
