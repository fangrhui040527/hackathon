import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  Image,
  KeyboardAvoidingView,
  Modal,
  PanResponder,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import { useScan } from '../context/ScanContext';
import FoodBackground from '../components/FoodBackground';
import { styles } from './styles/PreviewScreen.styles';

export default function PreviewScreen({ navigation }) {
  const { image, setImage, healthNote, setHealthNote } = useScan();

  const [isSending, setIsSending] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [draftNote, setDraftNote] = useState('');

  // Send button animations
  const sendScale   = useRef(new Animated.Value(1)).current;
  const shimmerAnim = useRef(new Animated.Value(0)).current;

  // Shimmer sweep loop
  useEffect(() => {
    const shimmer = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmerAnim, { toValue: 1, duration: 1400, useNativeDriver: true }),
        Animated.delay(600),
      ])
    );
    shimmer.start();
    return () => shimmer.stop();
  }, []);

  const onSendPressIn  = () => Animated.spring(sendScale, { toValue: 0.94, useNativeDriver: true }).start();
  const onSendPressOut = () => Animated.spring(sendScale, { toValue: 1,    useNativeDriver: true }).start();

  // Swipe-down pan responder to close modal
  const sheetSlide   = useRef(new Animated.Value(500)).current;
  const backdropOpacity = useRef(new Animated.Value(0)).current;
  const sheetPan = useRef(new Animated.Value(0)).current;

  const openSheet = () => {
    sheetSlide.setValue(500);
    sheetPan.setValue(0);
    setModalVisible(true);
    Animated.parallel([
      Animated.spring(sheetSlide, { toValue: 0, useNativeDriver: true, damping: 22, stiffness: 180, mass: 0.8 }),
      Animated.timing(backdropOpacity, { toValue: 1, duration: 250, useNativeDriver: true }),
    ]).start();
  };

  const closeSheet = (callback) => {
    Animated.parallel([
      Animated.timing(sheetSlide, { toValue: 500, duration: 220, useNativeDriver: true }),
      Animated.timing(backdropOpacity, { toValue: 0, duration: 200, useNativeDriver: true }),
    ]).start(() => {
      setModalVisible(false);
      sheetPan.setValue(0);
      callback && callback();
    });
  };

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, g) => g.dy > 8,
      onPanResponderMove:  (_, g) => { if (g.dy > 0) sheetPan.setValue(g.dy); },
      onPanResponderRelease: (_, g) => {
        if (g.dy > 80) {
          closeSheet();
        } else {
          Animated.spring(sheetPan, { toValue: 0, useNativeDriver: true }).start();
        }
      },
    })
  ).current;

  // Reset sending state when screen re-focuses (e.g. user navigates back)
  useFocusEffect(
    useCallback(() => {
      setIsSending(false);
    }, []),
  );

  const openModal = () => {
    setDraftNote(healthNote);
    openSheet();
  };

  const handleSaveNote = () => {
    closeSheet(() => setHealthNote(draftNote.trim()));
  };

  const handleRetake = () => {
    navigation.navigate('Scan');
  };

  const handleSend = () => {
    setIsSending(true);
    navigation.navigate('Chat', { triggerAnalysis: true });
  };

  return (
    <View style={styles.container}>
      <FoodBackground />

      <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>

        {/* ── Header ───────────────────────────────────────────────────── */}
        <View style={styles.header}>
          <Pressable
            onPress={() => navigation.navigate('Scan')}
            style={styles.backBtn}
            hitSlop={12}
          >
            <Text style={styles.backArrow}>‹</Text>
          </Pressable>
          <Text style={styles.headerTitle}>Review Your Scan</Text>
          {/* Spacer mirrors backBtn width to keep title centred */}
          <View style={styles.headerSpacer} />
        </View>

        {/* ── Scrollable content ─────────────────────────────────────── */}
        <ScrollView
          contentContainerStyle={styles.scroll}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Image preview — full width */}
          <View style={styles.imageOuter}>
            <View style={styles.imageInner}>
              {image ? (
                <Image source={{ uri: image }} style={styles.image} />
              ) : (
                <View style={styles.imagePlaceholder}>
                  <Text style={styles.placeholderEmoji}>🍪</Text>
                </View>
              )}
            </View>
          </View>
        </ScrollView>

        {/* ── Health note ───────────────────────────────────────────────── */}
        <View style={styles.noteSection}>
          <View style={styles.noteSectionRow}>
            <Text style={styles.noteSectionLabel}>Your Health Note</Text>
            <Pressable onPress={healthNote ? () => setHealthNote('') : openModal} hitSlop={8}>
              <Text style={styles.editBtn}>{healthNote ? 'Clear' : '+ Add'}</Text>
            </Pressable>
          </View>

          {healthNote ? (
            <Pressable onPress={openModal} style={styles.noteCard}>
              <Text style={styles.noteCardText}>{healthNote}</Text>
              <Text style={styles.editHint}>Tap to edit</Text>
            </Pressable>
          ) : (
            <Pressable onPress={openModal} style={styles.noNoteRow}>
              <Text style={styles.noNoteText}>No health note added — tap to add one</Text>
            </Pressable>
          )}
        </View>

        {/* ── Bottom buttons ────────────────────────────────────────────── */}
        <View style={styles.buttons}>
          <Pressable onPress={handleRetake} style={styles.retakeBtn}>
            <Image
              source={require('../../assets/WRetake_Icon.png')}
              style={styles.retakeIcon}
            />
          </Pressable>

          <Animated.View style={[styles.sendWrapper, { transform: [{ scale: sendScale }] }]}>
            <Pressable
              onPress={handleSend}
              onPressIn={onSendPressIn}
              onPressOut={onSendPressOut}
              disabled={isSending}
              style={[styles.sendBtn, isSending && { opacity: 0.5 }]}
            >
              {/* Shimmer overlay */}
              {!isSending && (
                <Animated.View
                  pointerEvents="none"
                  style={[
                    StyleSheet.absoluteFill,
                    styles.shimmerOverlay,
                    {
                      transform: [{
                        translateX: shimmerAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: [-300, 300],
                        }),
                      }],
                    },
                  ]}
                >
                  <LinearGradient
                    colors={['transparent', 'rgba(255,255,255,0.22)', 'transparent']}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={{ flex: 1, width: 120 }}
                  />
                </Animated.View>
              )}
              {isSending ? (
                <View style={styles.sendingRow}>
                  <ActivityIndicator size="small" color="#d3d5d4" />
                  <Text style={[styles.sendBtnText, styles.sendingText]}>Sending...</Text>
                </View>
              ) : (
                <Text style={styles.sendBtnText}>Send for Analysis ✦</Text>
              )}
            </Pressable>
          </Animated.View>
        </View>

      </SafeAreaView>

      {/* ── Bottom-sheet modal (health note editor) ───────────────────── */}
      <Modal
        visible={modalVisible}
        transparent
        animationType="none"
        onRequestClose={() => closeSheet()}
      >
        <KeyboardAvoidingView
          style={styles.modalOuter}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          {/* Dim backdrop — tap to dismiss */}
          <Animated.View
            style={[StyleSheet.absoluteFill, styles.modalBackdrop, { opacity: backdropOpacity }]}
          >
            <Pressable style={StyleSheet.absoluteFill} onPress={() => closeSheet()} />
          </Animated.View>

          {/* Sheet */}
          <Animated.View
            style={[styles.modalSheet, { transform: [{ translateY: Animated.add(sheetSlide, sheetPan) }] }]}
            {...panResponder.panHandlers}
          >
            <View style={styles.modalHandle} />

            <Text style={styles.modalTitle}>{healthNote ? '📝 Edit Health Note' : '📝 Add Health Note'}</Text>
            <Text style={styles.modalSubtitle}>
              Mention dietary restrictions or health conditions so agents can
              tailor their analysis.
            </Text>

            <TextInput
              style={styles.modalInput}
              value={draftNote}
              onChangeText={setDraftNote}
              placeholder="e.g. I am diabetic, I have high blood pressure..."
              placeholderTextColor="#6B7280"
              multiline
              maxLength={200}
              textAlignVertical="top"
              autoFocus
            />

            <Pressable onPress={handleSaveNote}>
              <LinearGradient
                colors={['#d3d5d4', '#b8babc']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.modalSaveBtn}
              >
                <Text style={styles.modalSaveText}>Save Note</Text>
              </LinearGradient>
            </Pressable>
          </Animated.View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}
