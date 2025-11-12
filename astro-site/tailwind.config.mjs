import typography from "@tailwindcss/typography";

export default {
  content: ["./src/**/*.{astro,html,js,jsx,ts,tsx,vue,svelte,md}"],
  theme: {
    extend: {},
  },
  plugins: [typography],
};
