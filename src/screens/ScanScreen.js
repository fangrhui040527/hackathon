import React, { useEffect, useRef } from 'react';
import {
  Animated,
  Easing,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { LinearGradient } from 'expo-linear-gradient';
import { colors } from '../constants/colors';
import { useScan } from '../context/ScanContext';
import Background3D from '../components/Background3D';

// ─── Scanning frame constants ────────────────────────────────────────────────
const FRAME_SIZE = 260;
const CORNER_LEN = 28;
const CORNER_W   = 3;
const BRACKET_COLOR = '#7A3CF7';

// ─── Corner bracket (L-shaped) ──────────────────────────────────────────────
function CornerBracket({ top, left }) {
  const edge = {
    ...(top  ? { top: 0 }  : { bottom: 0 }),
    ...(left ? { left: 0 } : { right: 0 }),
  };
  const glow = {
    shadowColor: BRACKET_COLOR,
    shadowOpacity: 0.9,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 0 },
    elevation: 6,
  };
  return (
    <View style={[styles.bracketWrap, edge]}>
      <View style={[styles.bracketH, edge, glow]} />
      <View style={[styles.bracketV, edge, glow]} />
    </View>
  );
}

// ─── Main screen ─────────────────────────────────────────────────────────────
export default function ScanScreen({ navigation }) {
  const [permission, requestPermission] = useCameraPermissions();
  const { setImage, result } = useScan();
  const cameraRef = useRef(null);

  const scanAnim   = useRef(new Animated.Value(0)).current;
  const pressScale = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(scanAnim, {
        toValue: FRAME_SIZE - 2,
        duration: 2000,
        easing: Easing.linear,
        useNativeDriver: true,
      }),
    ).start();
  }, []);

  const onPressIn  = () =>
    Animated.spring(pressScale, { toValue: 0.96, useNativeDriver: true }).start();
  const onPressOut = () =>
    Animated.spring(pressScale, { toValue: 1,    useNativeDriver: true }).start();

  const handleTakePhoto = async () => {
    if (!cameraRef.current) return;
    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.8 });
      setImage(photo.uri);
      navigation.navigate('Preview');
    } catch (e) {
      console.error('Camera capture error:', e);
    }
  };

  const handleUploadPhoto = async () => {
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!res.canceled && res.assets?.[0]?.uri) {
      setImage(res.assets[0].uri);
      navigation.navigate('Preview');
    }
  };

  // ── Permission: still resolving ──────────────────────────────────────────
  if (!permission) {
    return <View style={styles.container}><Background3D /></View>;
  }

  // ── Permission: denied ───────────────────────────────────────────────────
  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Background3D />
        <SafeAreaView style={StyleSheet.absoluteFill}>
          <View style={styles.permContainer}>
            <Text style={styles.permEmoji}>📷</Text>
            <Text style={styles.permTitle}>Camera Access Needed</Text>
            <Text style={styles.permBody}>
              HealthScan needs your camera to capture nutrition labels for analysis.
            </Text>
            {permission.canAskAgain ? (
              <Pressable onPress={requestPermission} style={styles.permBtn}>
                <LinearGradient
                  colors={['#9B5DFF', '#7A3CF7']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.permBtnInner}
                >
                  <Text style={styles.permBtnText}>Allow Camera</Text>
                </LinearGradient>
              </Pressable>
            ) : (
              <Text style={styles.permDenied}>
                Camera permission was permanently denied. Please enable it in your device Settings.
              </Text>
            )}
          </View>
        </SafeAreaView>
      </View>
    );
  }

  // ── Camera UI ────────────────────────────────────────────────────────────
  return (
    <View style={styles.container}>
      <Background3D />
      <CameraView ref={cameraRef} style={StyleSheet.absoluteFill} facing="back" />

      <SafeAreaView style={styles.safeOverlay} edges={['top', 'bottom']}>

        {/* ── Header ────────────────────────────────────────────────────── */}
        <View style={styles.header}>
          {/* Back to chat */}
          <Pressable
            onPress={() => navigation.goBack()}
            style={styles.headerBtn}
            hitSlop={12}
          >
            <Text style={styles.backArrow}>‹</Text>
          </Pressable>

          <View style={styles.headerCenter}>
            <Text style={styles.appName}>HealthScan</Text>
            <Text style={styles.subtitle}>Point at the nutrition label</Text>
          </View>

          {/* Last scan pill */}
          {result ? (
            <Pressable
              style={styles.lastScanBtn}
              onPress={() => navigation.navigate('Result')}
              hitSlop={8}
            >
              <Text style={styles.lastScanText} numberOfLines={1}>
                {result.product} ›
              </Text>
            </Pressable>
          ) : (
            <View style={styles.headerBtn} />
          )}
        </View>

        {/* ── Scanning frame ────────────────────────────────────────────── */}
        <View style={styles.centerSection}>
          <View style={styles.scanFrame}>
            <CornerBracket top  left  />
            <CornerBracket top  left={false} />
            <CornerBracket top={false} left  />
            <CornerBracket top={false} left={false} />
            <Animated.View
              style={[styles.scanLine, { transform: [{ translateY: scanAnim }] }]}
            />
          </View>
          <Text style={styles.frameHint}>Align label inside the frame</Text>
        </View>

        {/* ── Bottom buttons ────────────────────────────────────────────── */}
        <View style={styles.bottomPanel}>
          {/* Take Photo — primary gradient button */}
          <Animated.View style={{ transform: [{ scale: pressScale }] }}>
            <Pressable
              onPress={handleTakePhoto}
              onPressIn={onPressIn}
              onPressOut={onPressOut}
            >
              <LinearGradient
                colors={['#9B5DFF', '#7A3CF7']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.button}
              >
                <Text style={styles.buttonText}>📷  Take Photo</Text>
              </LinearGradient>
            </Pressable>
          </Animated.View>

          {/* Upload Photo — outlined button */}
          <Pressable onPress={handleUploadPhoto} style={styles.uploadBtn}>
            <Text style={styles.uploadBtnText}>🖼️  Upload from Gallery</Text>
          </Pressable>

          <Text style={styles.tip}>You can review the photo before sending</Text>
        </View>

      </SafeAreaView>
    </View>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  safeOverlay: {
    flex: 1,
    justifyContent: 'space-between',
  },

  // ── Header ──
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: 'rgba(10,10,26,0.72)',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  headerBtn: {
    width: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backArrow: {
    color: colors.textPrimary,
    fontSize: 34,
    lineHeight: 38,
    fontWeight: '200',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  appName: {
    color: colors.textPrimary,
    fontSize: 20,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: 12,
    marginTop: 2,
  },
  lastScanBtn: {
    width: 44,
    alignItems: 'flex-end',
  },
  lastScanText: {
    color: colors.primary,
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'right',
  },

  // ── Center / frame ──
  centerSection: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  scanFrame: {
    width: FRAME_SIZE,
    height: FRAME_SIZE,
    overflow: 'hidden',
  },
  scanLine: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 2,
    backgroundColor: colors.cyan,
    shadowColor: colors.cyan,
    shadowOpacity: 1,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 0 },
  },
  frameHint: {
    color: 'rgba(255,255,255,0.45)',
    fontSize: 12,
  },

  // ── Corner brackets ──
  bracketWrap: {
    position: 'absolute',
    width: CORNER_LEN,
    height: CORNER_LEN,
  },
  bracketH: {
    position: 'absolute',
    width: CORNER_LEN,
    height: CORNER_W,
    backgroundColor: BRACKET_COLOR,
    borderRadius: 2,
  },
  bracketV: {
    position: 'absolute',
    width: CORNER_W,
    height: CORNER_LEN,
    backgroundColor: BRACKET_COLOR,
    borderRadius: 2,
  },

  // ── Bottom panel ──
  bottomPanel: {
    backgroundColor: 'rgba(10,10,26,0.88)',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    padding: 20,
    gap: 12,
  },
  button: {
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  uploadBtn: {
    height: 54,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  uploadBtnText: {
    color: colors.primary,
    fontSize: 16,
    fontWeight: '600',
  },
  tip: {
    color: colors.textSecondary,
    fontSize: 11,
    textAlign: 'center',
  },

  // ── Permission screen ──
  permContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
    gap: 16,
  },
  permEmoji: { fontSize: 64, marginBottom: 4 },
  permTitle: { color: colors.textPrimary, fontSize: 22, fontWeight: '700', textAlign: 'center' },
  permBody:  { color: colors.textSecondary, fontSize: 14, textAlign: 'center', lineHeight: 22 },
  permBtn:   { width: '100%', marginTop: 8, borderRadius: 16, overflow: 'hidden' },
  permBtnInner: { paddingVertical: 16, alignItems: 'center', borderRadius: 16 },
  permBtnText:  { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  permDenied:   { color: colors.warning, fontSize: 13, textAlign: 'center', lineHeight: 20, marginTop: 8 },
});
