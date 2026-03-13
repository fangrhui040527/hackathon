import React, { useCallback, useRef, useState } from 'react';
import {
  Animated,
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
import { useFocusEffect } from '@react-navigation/native';
import { colors } from '../constants/colors';
import { useScan } from '../context/ScanContext';
import Background3D from '../components/Background3D';
import { styles } from './styles/ScanScreen.styles';

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

  const pressScale = useRef(new Animated.Value(1)).current;
  const [torchOn, setTorchOn] = useState(false);

  // Turn torch off whenever screen loses focus
  useFocusEffect(
    useCallback(() => {
      return () => setTorchOn(false);
    }, []),
  );

  const onPressIn  = () =>
    Animated.spring(pressScale, { toValue: 0.92, useNativeDriver: true }).start();
  const onPressOut = () =>
    Animated.spring(pressScale, { toValue: 1, useNativeDriver: true }).start();

  const handleTakePhoto = async () => {
    if (!cameraRef.current) return;
    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.8 });
      setTorchOn(false);
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
      setTorchOn(false);
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
      <CameraView ref={cameraRef} style={StyleSheet.absoluteFill} facing="back" enableTorch={torchOn} />

      <SafeAreaView style={styles.safeOverlay} edges={['top', 'bottom']}>

        {/* ── Header ────────────────────────────────────────────────────── */}
        <View style={styles.header}>
          <Pressable
            onPress={() => navigation.navigate('Chat')}
            style={styles.headerBtn}
            hitSlop={12}
          >
            <Text style={styles.backArrow}>‹</Text>
          </Pressable>

          <View style={styles.headerCenter}>
            <Text style={styles.appName}>Scan nutrition label</Text>
          </View>

          <View style={styles.headerBtn} />
        </View>

        {/* ── Capture guide frame ──────────────────────────────────────── */}
        <View style={styles.frameArea}>
          <View style={styles.captureFrame}>
            <View style={[styles.corner, styles.cornerTL]} />
            <View style={[styles.corner, styles.cornerTR]} />
            <View style={[styles.corner, styles.cornerBL]} />
            <View style={[styles.corner, styles.cornerBR]} />
          </View>
          <Text style={styles.frameHint}>Fit nutrition label inside the frame</Text>
        </View>

        {/* ── Bottom shutter row ───────────────────────────────────────── */}
        <View style={styles.shutterRow}>

          {/* Gallery button — left */}
          <Pressable onPress={handleUploadPhoto} style={styles.galleryBtn} hitSlop={8}>
            <Image
              source={require('../../assets/BImage_Icon.png')}
              style={styles.galleryIcon}
            />
          </Pressable>

          {/* Shutter — center */}
          <Animated.View style={{ transform: [{ scale: pressScale }] }}>
            <Pressable
              onPress={handleTakePhoto}
              onPressIn={onPressIn}
              onPressOut={onPressOut}
              style={styles.shutterBtn}
            >
              <View style={styles.shutterInner} />
            </Pressable>
          </Animated.View>

          {/* Flashlight — right */}
          <Pressable onPress={() => setTorchOn(v => !v)} style={[styles.galleryBtn, torchOn && styles.galleryBtnActive]} hitSlop={8}>
            <Image
              source={require('../../assets/WFlashlight_Icon.png')}
              style={[styles.galleryIcon, torchOn && styles.torchIconActive]}
            />
          </Pressable>

        </View>

      </SafeAreaView>
    </View>
  );
}
