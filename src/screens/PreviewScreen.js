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
import { colors } from '../constants/colors';
import { useScan } from '../context/ScanContext';
import Background3D from '../components/Background3D';

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
      <Background3D />

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
            <Text style={styles.retakeBtnText}>🔄 Retake</Text>
          </Pressable>

          <Pressable
            onPress={handleSend}
            disabled={isSending}
            style={styles.sendWrapper}
          >
            <LinearGradient
              colors={isSending ? ['#5A2DB7', '#5A2DB7'] : ['#9B5DFF', '#7A3CF7']}
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
                <Text style={styles.sendBtnText}>✅ Send for Analysis</Text>
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
              placeholderTextColor={colors.textSecondary}
              multiline
              maxLength={200}
              textAlignVertical="top"
              autoFocus
            />

            <Pressable onPress={handleSaveNote}>
              <LinearGradient
                colors={['#9B5DFF', '#7A3CF7']}
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

// ─── Styles ──────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  safeArea: {
    flex: 1,
  },

  // ── Header ──
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  backBtn: {
    width: 40,
    alignItems: 'flex-start',
    justifyContent: 'center',
  },
  backArrow: {
    color: colors.textPrimary,
    fontSize: 34,
    lineHeight: 38,
    fontWeight: '200',
  },
  headerTitle: {
    flex: 1,
    color: colors.textPrimary,
    fontSize: 17,
    fontWeight: '700',
    textAlign: 'center',
  },
  headerSpacer: {
    width: 40,
  },

  // ── Scroll ──
  scroll: {
    padding: 20,
    gap: 16,
  },

  // ── Image preview ──
  imageOuter: {
    borderRadius: 20,
    // Shadow on outer view (not clipped)
    shadowColor: '#7A3CF7',
    shadowOpacity: 0.5,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 4 },
    elevation: 12,
  },
  imageInner: {
    borderRadius: 20,
    overflow: 'hidden',
    height: 280,
    backgroundColor: '#12122A',
  },
  image: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  imagePlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderEmoji: {
    fontSize: 72,
  },

  // ── Checklist card ──
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    overflow: 'hidden',
  },
  checkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 13,
    paddingHorizontal: 16,
    gap: 10,
  },
  checkRowDivider: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  checkMark: {
    fontSize: 16,
  },
  checkText: {
    flex: 1,
    color: colors.textSecondary,
    fontSize: 13,
    lineHeight: 18,
  },

  // ── Health note section ──
  noteSection: {
    gap: 10,
  },
  noteSectionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  noteSectionLabel: {
    color: colors.textPrimary,
    fontSize: 15,
    fontWeight: '700',
  },
  editBtn: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: '600',
  },
  noteCard: {
    backgroundColor: '#1A0A2E',
    borderWidth: 1,
    borderColor: 'rgba(195,166,255,0.3)',
    borderRadius: 14,
    padding: 14,
    gap: 8,
  },
  noteCardText: {
    color: '#C3A6FF',
    fontSize: 14,
    lineHeight: 21,
  },
  editHint: {
    color: 'rgba(195,166,255,0.45)',
    fontSize: 11,
  },
  noNoteRow: {
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 14,
    padding: 14,
  },
  noNoteText: {
    color: colors.textSecondary,
    fontSize: 14,
  },

  // ── Bottom buttons ──
  buttons: {
    padding: 20,
    paddingTop: 14,
    gap: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  retakeBtn: {
    height: 54,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  retakeBtnText: {
    color: colors.primary,
    fontSize: 16,
    fontWeight: '700',
  },
  sendWrapper: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  sendBtn: {
    height: 54,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  sendingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  sendingText: {
    opacity: 0.85,
  },

  // ── Modal (bottom sheet) ──
  modalOuter: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  modalBackdrop: {
    backgroundColor: 'rgba(0,0,0,0.55)',
  },
  modalSheet: {
    backgroundColor: '#16162E',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    borderWidth: 1,
    borderBottomWidth: 0,
    borderColor: colors.border,
    padding: 24,
    gap: 14,
  },
  modalHandle: {
    width: 40,
    height: 4,
    borderRadius: 99,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignSelf: 'center',
    marginBottom: 6,
  },
  modalTitle: {
    color: colors.textPrimary,
    fontSize: 18,
    fontWeight: '700',
  },
  modalSubtitle: {
    color: colors.textSecondary,
    fontSize: 13,
    lineHeight: 19,
    marginTop: -4,
  },
  modalInput: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.15)',
    borderRadius: 14,
    padding: 14,
    color: colors.textPrimary,
    fontSize: 14,
    minHeight: 100,
    maxHeight: 160,
  },
  modalSaveBtn: {
    height: 54,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalSaveText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
});
