import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1C2B3A",
        parchment: "#F4F2EA",
        "parchment-line": "#DCD6C6",
        paper: "#FFFFFF",
        brass: "#A0813F",
        "brass-dark": "#7C6430",
        sage: "#3F6B54",
        "sage-bg": "#E7EFE9",
        amber: "#B87A22",
        "amber-bg": "#F6EBD8",
        brick: "#8C3A2C",
        "brick-bg": "#F3E2DE",
      },
      fontFamily: {
        display: ["var(--font-display)", "serif"],
        body: ["var(--font-body)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
