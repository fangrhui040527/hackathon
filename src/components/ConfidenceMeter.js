import React, { useEffect, useRef } from 'react';
import { Animated, Easing, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

const AnimatedGradient = Animated.createAnimatedComponent(LinearGradient);

export default function ConfidenceMeter({ value = 0, color = '#7A3CF7' }) {
  const anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(anim, {
      toValue: value,
      duration: 1000,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
  }, [value]);

  const widthPercent = anim.interpolate({
    inputRange: [0, 100],
    outputRange: ['0%', '100%'],
  });

  return (
    <View style={styles.container}>
      {/* Label row */}
      <View style={styles.labelRow}>
        <Text style={styles.labelLeft}>Confidence</Text>
        <Text style={[styles.labelRight, { color }]}>{value}%</Text>
      </View>

      {/* Track */}
      <View style={styles.track}>
        <AnimatedGradient
          colors={[color, color + '99']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={[styles.fill, { width: widthPercent }]}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 6,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  labelLeft: {
    color: '#8888AA',
    fontSize: 12,
    fontWeight: '500',
  },
  labelRight: {
    fontSize: 12,
    fontWeight: '700',
  },
  track: {
    height: 6,
    borderRadius: 99,
    backgroundColor: 'rgba(255,255,255,0.1)',
    overflow: 'hidden',
  },
  fill: {
    height: 6,
    borderRadius: 99,
  },
});
