/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#080810',
          secondary: '#0F0F1A',
          card: 'rgba(255,255,255,0.04)',
        },
        brand: {
          purple: '#7C3AED',
          indigo: '#4F46E5',
          500: '#7C3AED',
        },
        income: '#10B981',
        investment: '#6366F1',
        expense: '#F43F5E',
        text: {
          primary: '#F1F5F9',
          secondary: '#64748B',
          muted: '#334155',
        },
        border: {
          DEFAULT: 'rgba(255,255,255,0.08)',
          hover: 'rgba(255,255,255,0.15)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        '2xl': '16px',
        '3xl': '24px',
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(135deg, #7C3AED, #4F46E5)',
        'gradient-income': 'linear-gradient(135deg, #10B981, #059669)',
        'gradient-invest': 'linear-gradient(135deg, #6366F1, #4338CA)',
        'gradient-expense': 'linear-gradient(135deg, #F43F5E, #E11D48)',
      },
      boxShadow: {
        'glow-purple': '0 0 30px rgba(124,58,237,0.15)',
        'glow-income': '0 0 20px rgba(16,185,129,0.15)',
        'glow-invest': '0 0 20px rgba(99,102,241,0.15)',
        'glow-expense': '0 0 20px rgba(244,63,94,0.15)',
        card: '0 4px 24px rgba(0,0,0,0.4)',
      },
    },
  },
  plugins: [],
}
