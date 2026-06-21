/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: '#38bdf8',
        surface: '#0b1524',
        panel: '#0f172a',
        border: 'rgba(148,163,184,0.18)',
      },
    },
  },
  plugins: [],
}
