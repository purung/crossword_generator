module.exports = {
  content: ["./src/**/*.{html,js,vue,ts}"],
  theme: {
    extend: {
      gridTemplateColumns: { 21: "repeat(21, minmax(0, 1fr))" },
    },
  },
  plugins: [],
};
