/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        hospital: {
          primary: '#0066cc',
          secondary: '#00a8e1',
          success: '#10b981',
          warning: '#f59e0b',
          error: '#ef4444',
        }
      },
      animation: {
        'pulse-subtle': 'pulse-subtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'listening': 'listening 1.5s ease-in-out infinite',
        'speaking': 'speaking 0.6s ease-in-out infinite',
      }
    },
  },
  plugins: [],
}
