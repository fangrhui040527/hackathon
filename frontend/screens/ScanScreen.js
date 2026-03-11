import React, { useEffect, useRef } from 'react';
import {
  Animated,
  Easing,
  Image,
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
import { styles, FRAME_SIZE, CORNER_LEN, CORNER_W, BRACKET_COLOR } from './styles/ScanScreen.styles';

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
      Animated.sequence([
        Animated.timing(scanAnim, {
          toValue: FRAME_SIZE - 2,
          duration: 1600,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(scanAnim, {
          toValue: 0,
          duration: 1600,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ]),
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
                  colors={['#d3d5d4', '#b8babc']}
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
          <View style={styles.bottomBtnsRow}>

            {/* Take Photo — left, cyan gradient */}
            <Animated.View style={[{ flex: 1 }, { transform: [{ scale: pressScale }] }]}>
              <Pressable
                onPress={handleTakePhoto}
                onPressIn={onPressIn}
                onPressOut={onPressOut}
                style={{ flex: 1 }}
              >
                <LinearGradient
                  colors={['#d3d5d4', '#b8babc']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={[styles.halfBtn, { flex: 1 }]}
                >
                  <Image
                    source={require('../../assets/WCamera_Icon.png')}
                    style={styles.cameraBtnIcon}
                  />
                  <Text style={styles.cameraBtnText}>Take Photo</Text>
                </LinearGradient>
              </Pressable>
            </Animated.View>

            {/* Upload — right, outlined */}
            <Pressable onPress={handleUploadPhoto} style={styles.uploadBtn}>
              <Image
                source={require('../../assets/WImage_Icon.png')}
                style={styles.uploadBtnIcon}
              />
              <Text style={styles.uploadBtnText}>Gallery</Text>
            </Pressable>

          </View>

          <Text style={styles.tip}>You can review the photo before sending</Text>
        </View>

      </SafeAreaView>
    </View>
  );
}
