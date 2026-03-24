import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#e8eef8",
          100: "#c5d4ef",
          500: "#1a4b8c",
          600: "#163f77",
          700: "#123362",
        },
        construction: {
          50: "#fff3e0",
          500: "#7a4a00",
        },
      },
      fontFamily: {
        sans: ["Pretendard", "Malgun Gothic", "Apple SD Gothic Neo", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
