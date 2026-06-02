/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        cream: { DEFAULT: "#FAF6EF", dark: "#F0E9DC" },
        terra: { light: "#D4845A", DEFAULT: "#B8622E", dark: "#8B4513" },
        sage: { light: "#8FAF7E", DEFAULT: "#6B9A56", dark: "#4A7A38" },
        warmGray: { light: "#C4B8A8", DEFAULT: "#9B8E7E", dark: "#6B5F52" },
        forest: "#2D4A22",
        amber: { light: "#F5C842", DEFAULT: "#E8A020" },
      },
      fontFamily: {
        display: ['"Playfair Display"', "Georgia", "serif"],
        body: ['"DM Sans"', "system-ui", "sans-serif"],
        mono: ['"DM Mono"', "monospace"],
      },
      backgroundImage: {
        grain:
          "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E\")",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: 0, transform: "translateY(24px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
        "fade-in": { from: { opacity: 0 }, to: { opacity: 1 } },
        shimmer: { "0%, 100%": { opacity: 0.6 }, "50%": { opacity: 1 } },
        "bounce-dot": {
          "0%, 80%, 100%": { transform: "scale(0)" },
          "40%": { transform: "scale(1)" },
        },
        "slide-in": {
          from: { opacity: 0, transform: "translateX(-16px)" },
          to: { opacity: 1, transform: "translateX(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.6s ease forwards",
        "fade-in": "fade-in 0.4s ease forwards",
        shimmer: "shimmer 1.8s ease-in-out infinite",
        "bounce-dot": "bounce-dot 1.4s ease-in-out infinite",
        "slide-in": "slide-in 0.4s ease forwards",
      },
      boxShadow: {
        warm: "0 4px 32px rgba(184,98,46,0.12)",
        card: "0 2px 16px rgba(107,95,82,0.10)",
        glow: "0 0 40px rgba(212,132,90,0.25)",
      },
      borderRadius: { "2xl": "1rem", "3xl": "1.5rem", "4xl": "2rem" },
    },
  },
  plugins: [],
};
