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
        panel: "#ffffff",
        ink: "#172033",
        muted: "#667085",
        line: "#d9e2ec",
        accent: "#2563eb",
        good: "#15803d",
        warn: "#b45309",
        bad: "#b91c1c"
      }
    }
  },
  plugins: []
};

export default config;
