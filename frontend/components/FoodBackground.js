import React, { useCallback, useEffect, useRef } from 'react';
import { Dimensions, StyleSheet } from 'react-native';
import Animated, { useSharedValue, useAnimatedStyle } from 'react-native-reanimated';

const { width, height } = Dimensions.get('window');
const TWO_PI = Math.PI * 2;

// ─── Food emoji pool ──────────────────────────────────────────────────────────
const FOODS = [
  '🍔', '🍟', '🥗', '🥔', '🌮', '🍕',
  '🥪', '🥦', '🍎', '🥕', '🧀', '🌽',
  '🥑', '🍅', '🧅', '🥩', '🫐', '🍇',
  '🥚', '🥝', '🌶️', '🫑',
];

// ─── Physics constants ────────────────────────────────────────────────────────
const MIN_SPEED = 1.0;  // px/frame — smooth & graceful
const MAX_SPEED = 2.0;

// ─── Stable visual descriptors (generated once at module load) ────────────────
const DESCRIPTORS = Array.from({ length: 22 }, (_, i) => ({
  food:    FOODS[i % FOODS.length],
  size:    14 + Math.floor(Math.random() * 18), // 14–32 px
  opacity: 0.10 + Math.random() * 0.08,         // 0.10–0.18 (subtle, won't interrupt UI)
}));

// ─── Stable initial physics state (module-level, never re-randomised) ─────────
const INIT = DESCRIPTORS.map(d => {
  const angle = Math.random() * TWO_PI;
  const speed = MIN_SPEED + Math.random() * (MAX_SPEED - MIN_SPEED);
  return {
    x:      d.size + Math.random() * (width  - d.size * 2),
    y:      d.size + Math.random() * (height - d.size * 2),
    vx:     Math.cos(angle) * speed,
    vy:     Math.sin(angle) * speed,
    rot:    Math.random() * 360,
    rotSpd: (Math.random() < 0.5 ? 1 : -1) * (0.3 + Math.random() * 0.6),
  };
});

// ─── Single particle — owns its Reanimated shared values ─────────────────────
// useSharedValue is a hook and must live at the top level of a component,
// so each Particle manages its own values and exposes them via onMounted.
function Particle({ idx, descriptor, onMounted }) {
  const sx   = useSharedValue(INIT[idx].x);
  const sy   = useSharedValue(INIT[idx].y);
  const srot = useSharedValue(INIT[idx].rot);

  // Hand refs to the parent RAF loop once, on mount
  useEffect(() => { onMounted(idx, sx, sy, srot); }, []);

  // useAnimatedStyle runs entirely on the UI thread → butter-smooth rendering
  const animStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: sx.value },
      { translateY: sy.value },
      { rotate: `${srot.value}deg` },
    ],
  }));

  return (
    <Animated.Text
      style={[
        styles.particle,
        { fontSize: descriptor.size, opacity: descriptor.opacity },
        animStyle,
      ]}
    >
      {descriptor.food}
    </Animated.Text>
  );
}

// ─── Main export ──────────────────────────────────────────────────────────────
export default function FoodBackground() {
  // Slot for each particle's shared values, filled via onMounted
  const svRefs  = useRef(new Array(DESCRIPTORS.length).fill(null));

  // Mutable JS physics state — copy of INIT so it resets cleanly on remount
  const physics = useRef(INIT.map(p => ({ ...p }))).current;

  const onMounted = useCallback((idx, sx, sy, srot) => {
    svRefs.current[idx] = { sx, sy, srot };
  }, []);

  useEffect(() => {
    let rafId;

    const tick = () => {
      DESCRIPTORS.forEach((d, i) => {
        const refs = svRefs.current[i];
        if (!refs) return; // particle not yet mounted

        const p  = physics[i];
        const sz = d.size;

        p.x += p.vx;
        p.y += p.vy;

        // ── Wall bounce ──
        if      (p.x <= 0)           { p.x = 0;           p.vx =  Math.abs(p.vx); }
        else if (p.x >= width - sz)  { p.x = width - sz;  p.vx = -Math.abs(p.vx); }
        if      (p.y <= 0)           { p.y = 0;           p.vy =  Math.abs(p.vy); }
        else if (p.y >= height - sz) { p.y = height - sz; p.vy = -Math.abs(p.vy); }

        p.rot += p.rotSpd;

        // Writing shared values from JS — Reanimated flushes to UI thread each frame
        refs.sx.value   = p.x;
        refs.sy.value   = p.y;
        refs.srot.value = p.rot;
      });

      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, []);

  return (
    <>
      {DESCRIPTORS.map((d, i) => (
        <Particle key={i} idx={i} descriptor={d} onMounted={onMounted} />
      ))}
    </>
  );
}

const styles = StyleSheet.create({
  particle: {
    position:      'absolute',
    top:           0,
    left:          0,
    pointerEvents: 'none',
  },
});
