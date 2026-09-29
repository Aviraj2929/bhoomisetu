/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: '#1a3a6b', dark: '#12294d', light: '#e8eef8' },
        saffron: { DEFAULT: '#ff9933', dark: '#e67e00' },
        india: { green: '#138808', greenLight: '#e6f4e4' },
        ink: '#1f2937',
        line: '#c9d1dc',
        paper: '#f4f6f9',
        alert: '#b42318',
        warn: '#b45309',
      },
      fontFamily: {
        sans: ['"Noto Sans"', '"Noto Sans Devanagari"', 'Arial', 'sans-serif'],
      },
      borderRadius: { none: '0', sm: '2px', DEFAULT: '3px' },
    },
  },
  plugins: [],
}
