/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        banana: {
          50: '#FFF9E6',
          100: '#FFF0C2',
          200: '#FFE699',
          300: '#FFD966',
          400: '#FFCC33',
          500: '#E6B800',
          600: '#B38F00',
          700: '#806600',
          800: '#4D3D00',
          900: '#1A1400',
        },
        dark: {
          50: '#2A2A2A',
          100: '#252525',
          200: '#202020',
          300: '#1A1A1A',
          400: '#151515',
          500: '#121212',
          600: '#0F0F0F',
          700: '#0A0A0A',
          800: '#050505',
          900: '#000000',
        },
        surface: {
          DEFAULT: '#1E1E1E',
          light: '#2A2A2A',
          lighter: '#333333',
        },
        sidebar: {
          DEFAULT: '#161616',
          hover: '#1C1C1C',
          active: '#222222',
          border: '#2A2A2A',
        },
        muted: {
          DEFAULT: '#737373',
          foreground: '#A3A3A3',
        },
        accent: {
          DEFAULT: '#E6B800',
          foreground: '#121212',
          muted: 'rgba(230, 184, 0, 0.12)',
        },
        destructive: {
          DEFAULT: '#EF4444',
          foreground: '#FFFFFF',
          muted: 'rgba(239, 68, 68, 0.12)',
        },
        success: {
          DEFAULT: '#22C55E',
          foreground: '#FFFFFF',
          muted: 'rgba(34, 197, 94, 0.12)',
        },
        warning: {
          DEFAULT: '#F59E0B',
          foreground: '#121212',
          muted: 'rgba(245, 158, 11, 0.12)',
        },
        info: {
          DEFAULT: '#3B82F6',
          foreground: '#FFFFFF',
          muted: 'rgba(59, 130, 246, 0.12)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        '4xl': '2rem',
      },
      boxShadow: {
        'soft': '0 4px 24px rgba(0, 0, 0, 0.4)',
        'glow': '0 0 20px rgba(230, 184, 0, 0.15)',
        'glow-sm': '0 0 10px rgba(230, 184, 0, 0.1)',
        'elevated': '0 8px 32px rgba(0, 0, 0, 0.5)',
        'inner-light': 'inset 0 1px 0 rgba(255, 255, 255, 0.05)',
      },
      animation: {
        'shimmer': 'shimmer 2s ease-in-out infinite',
        'pulse-soft': 'pulse-soft 2s ease-in-out infinite',
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-in-left': 'slide-in-left 0.3s ease-out',
        'slide-in-up': 'slide-in-up 0.2s ease-out',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: 0.4 },
          '50%': { opacity: 0.7 },
        },
        'fade-in': {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        'slide-in-left': {
          '0%': { opacity: 0, transform: 'translateX(-12px)' },
          '100%': { opacity: 1, transform: 'translateX(0)' },
        },
        'slide-in-up': {
          '0%': { opacity: 0, transform: 'translateY(8px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      },
      spacing: {
        'sidebar': '260px',
        'topbar': '64px',
      },
    },
  },
  plugins: [],
}
