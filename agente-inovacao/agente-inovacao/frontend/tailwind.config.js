/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        totvs: {
          primary: '#00A1E0',
          secondary: '#003D73',
          accent: '#00D4AA',
          dark: '#1A1A2E',
          light: '#F8FAFC'
        }
      },
      fontFamily: {
        sans: ['Outfit', 'system-ui', 'sans-serif'],
        display: ['Sora', 'system-ui', 'sans-serif']
      }
    },
  },
  plugins: [],
}
