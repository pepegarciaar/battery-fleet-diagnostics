import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./lib/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        panel: "#f7f7f7",
        ink: "#222222",
        muted: "#858585",
        line: "#d8d8d8",
        accent: "#d80000",
        good: "#888888",
        warn: "#222222",
        bad: "#d80000"
      }
    }
  },
  plugins: []
};

export default config;
