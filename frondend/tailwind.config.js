/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Python Theme Colors
        'bg-primary': '#0b1320',    // Very dark navy blue
        'bg-surface': '#111d2e',    // Dark blue
        'bg-elevated': '#16273d',   // Slightly lighter blue
        'border': '#203650',        // Border blue
        'ink-primary': '#f8fafc',   // Slate 50
        'ink-secondary': '#cbd5e1', // Slate 300
        'ink-muted': '#64748b',     // Slate 500
        'accent': '#FFD43B',        // Python Yellow
        'accent-hover': '#FCE883',  // Lighter Yellow
        'accent-blue': '#3776AB',   // Python Blue
        'code': '#080e17',          // Darker for code blocks
        'success': '#10b981',
        'danger': '#ef4444',
        'warning': '#f59e0b',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"Fira Code"', 'monospace'],
      },
      boxShadow: {
        'glow': '0 0 20px rgba(255, 212, 59, 0.15)',
        'glow-lg': '0 0 30px rgba(255, 212, 59, 0.25)',
      },
      backgroundImage: {
        'radial-glow': 'radial-gradient(circle at 50% 0%, rgba(55, 118, 171, 0.2), transparent 60%)',
      }
    },
  },
  plugins: [],
}