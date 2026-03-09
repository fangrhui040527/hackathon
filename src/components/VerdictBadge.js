import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const VERDICT_MAP = {
  safe: {
    label: 'Safe',
    emoji: '✅',
    bg: '#0A2E1A',
    color: '#00B341',
    border: '#00B34133',
  },
  caution: {
    label: 'Caution',
    emoji: '⚠️',
    bg: '#2E1A00',
    color: '#E6A817',
    border: '#E6A81733',
  },
  avoid: {
    label: 'Avoid',
    emoji: '🚫',
    bg: '#2E0A0A',
    color: '#E53935',
    border: '#E5393533',
  },
};

export default function VerdictBadge({ verdict, small }) {
  const v = VERDICT_MAP[verdict] ?? VERDICT_MAP.caution;

  return (
    <View
      style={[
        styles.badge,
        { backgroundColor: v.bg, borderColor: v.border },
        small && styles.badgeSmall,
      ]}
    >
      <Text style={[styles.text, { color: v.color }, small && styles.textSmall]}>
        {v.emoji} {v.label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    alignSelf: 'flex-start',
  },
  badgeSmall: {
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  text: {
    fontSize: 13,
    fontWeight: '700',
  },
  textSmall: {
    fontSize: 11,
  },
});
