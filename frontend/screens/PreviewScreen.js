import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  KeyboardAvoidingView,
  Modal,
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

const CHECKLIST = [
  'Nutrition label or ingredients list is visible',
  'Text is readable and not blurry',
  'Label is not cut off at edges',
];

export default function PreviewScreen({ navigation }) {
  const { image, setImage, healthNote, setHealthNote } = useScan();

  const [isSending, setIsSending] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [draftNote, setDraftNote] = useState('');

  // Reset sending state when screen re-focuses (e.g. user navigates back)
  useFocusEffect(
    useCallback(() => {
      setIsSending(false);
    }, []),
  );

  const openModal = () => {
    setDraftNote(healthNote);
    setModalVisible(true);
  };

  const handleSaveNote = () => {
    setHealthNote(draftNote.trim());
    setModalVisible(false);
  };

  const handleRetake = () => {
    setImage(null);
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
            onPress={() => navigation.goBack()}
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
          {/* Image preview */}
          {/* Shadow lives on outer View; clip lives on inner View */}
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

          {/* Visual checklist */}
          <View style={styles.card}>
            {CHECKLIST.map((item, i) => (
              <View
                key={i}
                style={[styles.checkRow, i > 0 && styles.checkRowDivider]}
              >
                <Text style={styles.checkMark}>✅</Text>
                <Text style={styles.checkText}>{item}</Text>
              </View>
            ))}
          </View>

          {/* Health note section */}
          <View style={styles.noteSection}>
            <View style={styles.noteSectionRow}>
              <Text style={styles.noteSectionLabel}>📝 Your Health Note</Text>
              <Pressable onPress={openModal} hitSlop={8}>
                <Text style={styles.editBtn}>{healthNote ? '✏️ Edit' : '+ Add'}</Text>
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
        </ScrollView>

        {/* ── Bottom buttons ────────────────────────────────────────────── */}
        <View style={styles.buttons}>
          <Pressable onPress={handleRetake} style={styles.retakeBtn}>
            <Text style={styles.retakeBtnText}>Retake</Text>
          </Pressable>

          <Pressable
            onPress={handleSend}
            disabled={isSending}
            style={styles.sendWrapper}
          >
            <LinearGradient
              colors={isSending ? ['rgba(211,213,212,0.3)', 'rgba(211,213,212,0.3)'] : ['#d3d5d4', '#b8babc']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.sendBtn}
            >
              {isSending ? (
                <View style={styles.sendingRow}>
                  <ActivityIndicator size="small" color="#fff" />
                  <Text style={[styles.sendBtnText, styles.sendingText]}>
                    Sending...
                  </Text>
                </View>
              ) : (
                <Text style={styles.sendBtnText}>Send for Analysis</Text>
              )}
            </LinearGradient>
          </Pressable>
        </View>

      </SafeAreaView>

      {/* ── Bottom-sheet modal (health note editor) ───────────────────── */}
      <Modal
        visible={modalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setModalVisible(false)}
      >
        <KeyboardAvoidingView
          style={styles.modalOuter}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          {/* Dim backdrop — tap to dismiss */}
          <Pressable
            style={[StyleSheet.absoluteFill, styles.modalBackdrop]}
            onPress={() => setModalVisible(false)}
          />

          {/* Sheet */}
          <View style={styles.modalSheet}>
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
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}
