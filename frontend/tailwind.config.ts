import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: "#111111", soft: "#333333", mute: "#444444" },
        paper: "#FBFBF7",
        rule: "#E4E4DC",
        card: "#FFFFFF",
        blue: { DEFAULT: "#003087", mid: "#0070BA" },
        cyan: { DEFAULT: "#009CDE" },
        yellow: { DEFAULT: "#FFC439" },
        pink: { DEFAULT: "#FF5FA2" },
        green: { DEFAULT: "#4ADE9A" },
        mint: "#C9F2DD",
        rose: "#FFC2DD",
        butter: "#FFE9A8",
        sky: "#BFE6F7",
        blush: "#FFB3B0",
        step: "#D9D9D9",
        skeleton: "#EFEFE8",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
        pixel: ["Silkscreen", "monospace"],
        hand: ["Gaegu", "cursive"],
      },
      borderRadius: { DEFAULT: "2px", tag: "3px" },
      borderWidth: { DEFAULT: "2px" },
      boxShadow: {
        "hard-sm": "3px 3px 0 #111111",
        hard: "4px 4px 0 #111111",
        "hard-lg": "6px 6px 0 #111111",
      },
      rotate: { "2": "2deg", "1.5": "1.5deg", "1": "1deg", "-1": "-1deg", "-1.5": "-1.5deg", "-2": "-2deg" },
    },
  },
  plugins: [],
} satisfies Config;
