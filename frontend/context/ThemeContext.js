import React, { createContext, useContext, useState } from 'react';

// ─── Palette definitions ──────────────────────────────────────────────────────
export const DARK_PALETTE = {
  deep:     '#0d131a',
  surface:  '#141c26',
  surface2: '#333740',
  border:   'rgba(255,255,255,0.07)',
  borderMd: 'rgba(255,255,255,0.11)',
  accent:   '#d3d5d4',
  text1:    '#E8ECF4',
  text2:    '#6B7280',
  text3:    'rgba(232,236,244,0.45)',
};

export const LIGHT_PALETTE = {
  deep:     '#FFFFFF',    // white background
  surface:  '#F0F0F0',    // light grey for header/footer panels
  surface2: '#333740',    // dark charcoal containers (same as dark mode — intentional)
  border:   'rgba(0,0,0,0.08)',
  borderMd: 'rgba(0,0,0,0.14)',
  accent:   '#E8E8E8',    // near-white for buttons
  text1:    '#0d131a',    // dark text on silver bg
  text2:    '#4A4E58',    // secondary text
  text3:    'rgba(13,19,26,0.45)',
};

// ─── Context ──────────────────────────────────────────────────────────────────
const ThemeContext = createContext({
  isDark: true,
  palette: DARK_PALETTE,
  toggleTheme: () => {},
});

export function ThemeProvider({ children }) {
  const [isDark, setIsDark] = useState(true);

  const toggleTheme = () => setIsDark(v => !v);

  return (
    <ThemeContext.Provider value={{ isDark, palette: isDark ? DARK_PALETTE : LIGHT_PALETTE, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
