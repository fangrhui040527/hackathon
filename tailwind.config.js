module.exports = {
  content: [
    './App.{js,jsx,ts,tsx}',
    './src/**/*.{js,jsx,ts,tsx}',   // ← your src folder
  ],
  presets: [require('nativewind/preset')],  // ← required for v4
  theme: {
    extend: {},
  },
  plugins: [],
};