/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary:  "#0a0a0f",
          surface:  "#111118",
          elevated: "#1a1a24",
        },
        border: {
          DEFAULT: "#2a2a3a",
          subtle:  "#1e1e2e",
        },
        accent: {
          DEFAULT: "#7c6af7",
          hover:   "#9585f9",
          glow:    "#7c6af733",
        },
        success: "#22d3a0",
        warning: "#f59e0b",
        danger:  "#f43f5e",
        ink: {
          primary:   "#f1f0ff",
          secondary: "#8b8aa8",
          muted:     "#4a4a6a",
        },
        code: "#0d0d16",
      },
      fontFamily: {
        display: ["Syne", "sans-serif"],
        body:    ["DM Sans", "sans-serif"],
        mono:    ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        glow:    "0 0 20px #7c6af733",
        "glow-lg": "0 0 40px #7c6af755",
      },
      backgroundImage: {
        "radial-glow": "radial-gradient(ellipse at center, #7c6af715 0%, transparent 70%)",
      },
      animation: {
        "fade-in":    "fadeIn 0.4s ease forwards",
        "slide-up":   "slideUp 0.4s ease forwards",
        "spin-slow":  "spin 2s linear infinite",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn:    { "0%": { opacity: 0 }, "100%": { opacity: 1 } },
        slideUp:   { "0%": { opacity: 0, transform: "translateY(16px)" }, "100%": { opacity: 1, transform: "translateY(0)" } },
        pulseGlow: { "0%, 100%": { boxShadow: "0 0 10px #7c6af733" }, "50%": { boxShadow: "0 0 30px #7c6af766" } },
      },
    },
  },
  plugins: [],
}
