/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        base: '#070b13',
        surface: '#0d1421',
        elevated: '#131d2e',
        border: '#1e2d42',
        accent: '#22d3ee',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Cascadia Code', 'monospace'],
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
