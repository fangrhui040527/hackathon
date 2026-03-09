import React, { useEffect } from 'react';
import { Dimensions, StyleSheet } from 'react-native';
import { Canvas, Path, Skia } from '@shopify/react-native-skia';
import {
  useDerivedValue,
  useSharedValue,
  withRepeat,
  withTiming,
  Easing,
} from 'react-native-reanimated';

const { width, height } = Dimensions.get('window');

const DOT_COUNT = 40;
const CONNECT_DIST_SQ = 120 * 120;
const DRIFT = 50;
const TWO_PI = Math.PI * 2;

// Food colour buckets: tomato · green-apple · orange · blueberry
// (mapped by i % 4 → colorType 0-3)
const DOT_RADIUS = [3, 4, 3, 5]; // vary dot size per colour type

// Pre-generate dot descriptors at module load (stable across renders)
const DOT_DATA = Array.from({ length: DOT_COUNT }, (_, i) => ({
  baseX: Math.random() * width,
  baseY: Math.random() * height,
  sx: 0.3 + Math.random() * 0.7, // x oscillation speed (cycles per loop)
  sy: 0.3 + Math.random() * 0.7, // y oscillation speed
  px: Math.random() * TWO_PI,    // x phase offset
  py: Math.random() * TWO_PI,    // y phase offset
  colorType: i % 4,              // 0=tomato 1=apple 2=orange 3=berry
}));

export default function Background3D({ children }) {
  // t goes 0 → 1 linearly in 20 s, loops forever
  const t = useSharedValue(0);

  useEffect(() => {
    t.value = withRepeat(
      withTiming(1, { duration: 20000, easing: Easing.linear }),
      -1,
      false,
    );
  }, []);

  // Compute all dot positions from t once per frame
  const positions = useDerivedValue(() =>
    DOT_DATA.map(d => ({
      x: d.baseX + DRIFT * Math.sin(TWO_PI * t.value * d.sx + d.px),
      y: d.baseY + DRIFT * Math.cos(TWO_PI * t.value * d.sy + d.py),
    }))
  );

  // Lines between dots closer than 120 px
  const linesPath = useDerivedValue(() => {
    const pos = positions.value;
    const p = Skia.Path.Make();
    for (let i = 0; i < pos.length; i++) {
      for (let j = i + 1; j < pos.length; j++) {
        const dx = pos[i].x - pos[j].x;
        const dy = pos[i].y - pos[j].y;
        if (dx * dx + dy * dy < CONNECT_DIST_SQ) {
          p.moveTo(pos[i].x, pos[i].y);
          p.lineTo(pos[j].x, pos[j].y);
        }
      }
    }
    return p;
  }, [positions]);

  // Tomato-red dots (colorType 0)
  const tomatoPath = useDerivedValue(() => {
    const pos = positions.value;
    const p = Skia.Path.Make();
    for (let i = 0; i < DOT_DATA.length; i++) {
      if (DOT_DATA[i].colorType === 0) p.addCircle(pos[i].x, pos[i].y, DOT_RADIUS[0]);
    }
    return p;
  }, [positions]);

  // Apple-green dots (colorType 1)
  const greenPath = useDerivedValue(() => {
    const pos = positions.value;
    const p = Skia.Path.Make();
    for (let i = 0; i < DOT_DATA.length; i++) {
      if (DOT_DATA[i].colorType === 1) p.addCircle(pos[i].x, pos[i].y, DOT_RADIUS[1]);
    }
    return p;
  }, [positions]);

  // Orange dots (colorType 2)
  const orangePath = useDerivedValue(() => {
    const pos = positions.value;
    const p = Skia.Path.Make();
    for (let i = 0; i < DOT_DATA.length; i++) {
      if (DOT_DATA[i].colorType === 2) p.addCircle(pos[i].x, pos[i].y, DOT_RADIUS[2]);
    }
    return p;
  }, [positions]);

  // Berry-purple dots (colorType 3)
  const berryPath = useDerivedValue(() => {
    const pos = positions.value;
    const p = Skia.Path.Make();
    for (let i = 0; i < DOT_DATA.length; i++) {
      if (DOT_DATA[i].colorType === 3) p.addCircle(pos[i].x, pos[i].y, DOT_RADIUS[3]);
    }
    return p;
  }, [positions]);

  return (
    <>
      <Canvas style={[StyleSheet.absoluteFill, { zIndex: 0 }]}>
        {/* Warm golden connecting lines */}
        <Path
          path={linesPath}
          color="rgba(255,165,0,0.12)"
          style="stroke"
          strokeWidth={1}
        />
        {/* Food-coloured dots */}
        <Path path={tomatoPath} color="rgba(231,76,60,0.5)" />
        <Path path={greenPath}  color="rgba(46,204,113,0.5)" />
        <Path path={orangePath} color="rgba(243,156,18,0.5)" />
        <Path path={berryPath}  color="rgba(155,89,182,0.5)" />
      </Canvas>
      {children}
    </>
  );
}
