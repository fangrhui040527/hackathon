module.exports = {
  content: [
    './App.{js,jsx,ts,tsx}',
    './frontend/**/*.{js,jsx,ts,tsx}',   // ← your frontend folder
  ],
  presets: [require('nativewind/preset')],  // ← required for v4
  theme: {
    extend: {},
  },
  plugins: [],
};