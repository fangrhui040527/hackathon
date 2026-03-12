import React, { useRef, useEffect, useState } from 'react';
import {
  Modal,
  Animated,
  Dimensions,
  Pressable,
  View,
  Text,
  Image,
  ScrollView,
  StyleSheet,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../context/ThemeContext';

const { width: SCREEN_W } = Dimensions.get('window');
const DRAWER_W = Math.min(SCREEN_W * 0.82, 320);

// ─── Single menu row ──────────────────────────────────────────────────────────
function MenuItem({ icon, iconImg, label, sub, isDark, onPress, rightEl }) {
  const [pressed, setPressed] = useState(false);
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const onPressIn = () => {
    setPressed(true);
    Animated.spring(scaleAnim, { toValue: 0.97, useNativeDriver: true, tension: 200, friction: 10 }).start();
  };
  const onPressOut = () => {
    setPressed(false);
    Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, tension: 200, friction: 10 }).start();
  };

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        onPress={onPress}
        style={[
          s.menuItem,
          {
            backgroundColor: pressed
              ? (isDark ? 'rgba(255,255,255,0.09)' : 'rgba(0,0,0,0.06)')
              : (isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)'),
            borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
          },
        ]}
      >
        <View style={[s.iconWrap, { backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)' }]}>
          {iconImg
            ? <Image source={iconImg} style={[s.menuIconImg, { tintColor: isDark ? '#FFFFFF' : '#0d131a' }]} />
            : <Text style={s.iconText}>{icon}</Text>}
        </View>
        <View style={{ flex: 1, gap: 2 }}>
          <Text style={[s.menuLabel, { color: isDark ? '#E8ECF4' : '#0d131a' }]}>{label}</Text>
          {sub ? <Text style={[s.menuSub, { color: isDark ? '#6B7280' : '#9CA3AF' }]}>{sub}</Text> : null}
        </View>
        {rightEl ?? <Text style={{ color: isDark ? '#4B5563' : '#C0C4CC', fontSize: 18 }}>›</Text>}
      </Pressable>
    </Animated.View>
  );
}

// ─── Section label ────────────────────────────────────────────────────────────
function SectionLabel({ label, isDark }) {
  return (
    <Text style={[s.sectionLabel, { color: isDark ? '#4B5563' : '#9CA3AF' }]}>{label}</Text>
  );
}

// ─── Divider ─────────────────────────────────────────────────────────────────
function Divider({ isDark }) {
  return (
    <View style={[s.divider, { backgroundColor: isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.07)' }]} />
  );
}

// ─── Animated toggle switch ───────────────────────────────────────────────────
function ToggleSwitch({ value, onToggle, isDark }) {
  const anim = useRef(new Animated.Value(value ? 1 : 0)).current;

  useEffect(() => {
    Animated.spring(anim, {
      toValue: value ? 1 : 0,
      useNativeDriver: false,
      tension: 180,
      friction: 11,
    }).start();
  }, [value]);

  const trackColor = anim.interpolate({
    inputRange: [0, 1],
    outputRange: ['#D1D5DB', '#2a3a52'],
  });
  const knobX = anim.interpolate({ inputRange: [0, 1], outputRange: [2, 24] });
  const knobColor = anim.interpolate({
    inputRange: [0, 1],
    outputRange: ['#ffffff', '#d3d5d4'],
  });

  return (
    <Pressable onPress={onToggle} hitSlop={8}>
      <Animated.View style={[s.track, { backgroundColor: trackColor }]}>
        <Animated.View
          style={[
            s.knob,
            { transform: [{ translateX: knobX }], backgroundColor: knobColor },
          ]}
        />
      </Animated.View>
    </Pressable>
  );
}

// ─── Main drawer ──────────────────────────────────────────────────────────────
export default function BurgerMenu({ visible, onClose, navigation, onClearChat }) {
  const insets = useSafeAreaInsets();
  const { isDark, toggleTheme } = useTheme();

  const slideAnim = useRef(new Animated.Value(DRAWER_W)).current;
  const fadeAnim  = useRef(new Animated.Value(0)).current;
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (visible) {
      setMounted(true);
      Animated.parallel([
        Animated.spring(slideAnim, { toValue: 0, useNativeDriver: true, tension: 72, friction: 12 }),
        Animated.timing(fadeAnim,  { toValue: 1, duration: 240, useNativeDriver: true }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(slideAnim, { toValue: DRAWER_W, duration: 220, useNativeDriver: true }),
        Animated.timing(fadeAnim,  { toValue: 0, duration: 200, useNativeDriver: true }),
      ]).start(() => setMounted(false));
    }
  }, [visible]);

  if (!mounted) return null;

  const drawerBg     = isDark ? '#141c26' : '#FFFFFF';
  const drawerBorder = isDark ? 'rgba(255,255,255,0.09)' : 'rgba(0,0,0,0.09)';
  const appNameColor = isDark ? '#E8ECF4' : '#0d131a';
  const versionColor = isDark ? '#4B5563' : '#9CA3AF';
  const footerColor  = isDark ? '#2D3748' : '#D1D5DB';

  return (
    <Modal transparent visible={mounted} animationType="none" onRequestClose={onClose} statusBarTranslucent>
      {/* Dim backdrop */}
      <Animated.View style={[s.backdrop, { opacity: fadeAnim }]} pointerEvents="box-none">
        <Pressable style={{ flex: 1 }} onPress={onClose} />
      </Animated.View>

      {/* Sliding drawer */}
      <Animated.View
        style={[
          s.drawer,
          {
            width: DRAWER_W,
            backgroundColor: drawerBg,
            borderLeftColor: drawerBorder,
            paddingTop: insets.top + 16,
            paddingBottom: insets.bottom + 24,
            transform: [{ translateX: slideAnim }],
          },
        ]}
      >
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingHorizontal: 16, gap: 0 }}
        >
          {/* ── App header ── */}
          <View style={s.drawerHead}>
            <Image
              source={require('../../assets/HealthLensAI_Logo.png')}
              style={s.logoImg}
              resizeMode="contain"
            />

            <View style={{ flex: 1, gap: 3 }}>
              <Text style={[s.appName, { color: appNameColor }]}>HealthScan AI</Text>
              <Text style={[s.versionText, { color: versionColor }]}>6 AI Agents</Text>
            </View>

            <Pressable onPress={onClose} style={[s.closeBtn, { backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)' }]} hitSlop={8}>
              <Text style={{ color: isDark ? '#9CA3AF' : '#6B7280', fontSize: 16, lineHeight: 18 }}>✕</Text>
            </Pressable>
          </View>

          <Divider isDark={isDark} />

          {/* ── Navigation ── */}
          <SectionLabel label="NAVIGATION" isDark={isDark} />

          <MenuItem
            iconImg={require('../../assets/BCamera_Icon.png')}
            label="Scan a Product" sub="Open the camera scanner"
            isDark={isDark}
            onPress={() => { onClose(); setTimeout(() => navigation.navigate('Scan'), 260); }}
          />
          <MenuItem
            iconImg={require('../../assets/WNewChat_Icon.png')}
            label="New Conversation" sub="Clear chat and start fresh"
            isDark={isDark}
            onPress={() => { onClose(); setTimeout(onClearChat, 260); }}
          />
          <MenuItem
            iconImg={require('../../assets/WChatHistory_Icon.png')}
            label="Chat History" sub="View previous conversations"
            isDark={isDark}
            onPress={() => { onClose(); setTimeout(() => navigation.navigate('Chat'), 260); }}
          />

          <Divider isDark={isDark} />

          {/* ── Appearance ── */}
          <SectionLabel label="APPEARANCE" isDark={isDark} />

          {/* Theme toggle row — custom (not MenuItem) */}
          <View
            style={[
              s.menuItem,
              {
                backgroundColor: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)',
                borderColor:     isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
              },
            ]}
          >
            <View style={[s.iconWrap, { backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)' }]}>
              <Image
                source={isDark ? require('../../assets/WDark_Icon.png') : require('../../assets/WLight_Icon.png')}
                style={[s.menuIconImg, { tintColor: isDark ? '#FFFFFF' : '#0d131a' }]}
              />
            </View>
            <View style={{ flex: 1, gap: 2 }}>
              <Text style={[s.menuLabel, { color: isDark ? '#E8ECF4' : '#0d131a' }]}>
                {isDark ? 'Dark Mode' : 'Light Mode'}
              </Text>
              <Text style={[s.menuSub, { color: isDark ? '#6B7280' : '#9CA3AF' }]}>
                {isDark ? 'Easy on the eyes at night' : 'Bright and clean look'}
              </Text>
            </View>
            <ToggleSwitch value={isDark} onToggle={toggleTheme} isDark={isDark} />
          </View>

          <Divider isDark={isDark} />

          {/* ── About ── */}
          <SectionLabel label="ABOUT" isDark={isDark} />

          <MenuItem
            icon="ℹ️" label="About" sub="Built with 6 specialized AI agents"
            isDark={isDark}
            onPress={onClose}
          />

          {/* ── Footer ── */}
          <View style={s.footer}>
            <Text style={[s.footerText, { color: footerColor }]}>HEALTHSCAN AI  ·  2026</Text>
          </View>
        </ScrollView>
      </Animated.View>
    </Modal>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.55)',
  },
  drawer: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    borderLeftWidth: 1,
    shadowColor: '#000',
    shadowOpacity: 0.55,
    shadowRadius: 28,
    shadowOffset: { width: -6, height: 0 },
    elevation: 24,
  },
  drawerHead: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingBottom: 14,
    paddingTop: 4,
  },
  logoImg: {
    width: 48,
    height: 48,
    borderRadius: 12,
  },
  menuIconImg: {
    width: 40,
    height: 40,
    resizeMode: 'contain',
  },
  appName: {
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  versionText: {
    fontSize: 11,
    letterSpacing: 0.3,
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  divider: {
    height: 1,
    marginHorizontal: -16,
    marginVertical: 6,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.4,
    paddingHorizontal: 4,
    paddingTop: 10,
    paddingBottom: 6,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderRadius: 14,
    borderWidth: 1,
    paddingVertical: 12,
    paddingHorizontal: 14,
    marginBottom: 6,
  },
  iconWrap: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconText: {
    fontSize: 19,
  },
  menuLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.1,
  },
  menuSub: {
    fontSize: 11,
  },
  // Toggle switch
  track: {
    width: 50,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
  },
  knob: {
    width: 24,
    height: 24,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOpacity: 0.25,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 3,
  },
  footer: {
    marginTop: 20,
    marginBottom: 4,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1.5,
  },
});
