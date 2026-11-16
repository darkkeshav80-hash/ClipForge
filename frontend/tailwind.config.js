/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#080B14',
        surface: {
          DEFAULT: '#101525',
          dark: '#0A0E1A',
          card: 'rgba(255, 255, 255, 0.05)',
          border: 'rgba(255, 255, 255, 0.12)',
          hover: 'rgba(255, 255, 255, 0.08)',
        },
        forge: {
          purple: '#8B5CF6',
          blue: '#38BDF8',
          green: '#22C55E',
          red: '#EF4444',
          cyan: '#06B6D4',
          amber: '#F59E0B',
          pink: '#EC4899',
        }
      },
      backdropBlur: {
        xs: '2px',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 15px rgba(139, 92, 246, 0.2)' },
          '100%': { boxShadow: '0 0 30px rgba(56, 189, 248, 0.4)' },
        }
      }
    },
  },
  plugins: [],
}
