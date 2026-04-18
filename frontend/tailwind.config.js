/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Gumroad-inspired warm primary (orange) with supporting accents
        primary: {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316', // vivid orange
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12',
        },
        ink: '#111827', // deep text color
        paper: '#fefce8', // warm background
        accent: {
          yellow: '#facc15',
          pink: '#fb7185',
          teal: '#14b8a6',
          purple: '#a855f7',
        },
      },
      boxShadow: {
        brutal: '4px 4px 0 0 #111827',
        'brutal-sm': '3px 3px 0 0 #111827',
      },
      borderRadius: {
        brutal: '1.25rem',
      },
      fontFamily: {
        display: ['system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

