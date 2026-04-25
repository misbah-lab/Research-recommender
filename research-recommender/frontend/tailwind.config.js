/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Playfair Display"', 'serif'],
        body: ['"DM Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        ink: '#0d0d0d',
        paper: '#f5f0e8',
        accent: '#c8441a',
        muted: '#7a7065',
        highlight: '#f0e6d3',
        card: '#faf7f2',
      }
    }
  },
  plugins: []
}
