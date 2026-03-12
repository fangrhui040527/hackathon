import { StyleSheet } from 'react-native';

// ─── Enterprise dark palette (mirrors ScanScreen / ChatScreen) ────────────────
const DEEP      = '#0d131a';
const SURFACE   = '#141c26';
const SURFACE2  = '#333740';
const BORDER    = 'rgba(255,255,255,0.07)';
const BORDER_MD = 'rgba(255,255,255,0.11)';
const WHITESILVER     = '#d3d5d4';
const WHITESILVER_BDR = 'rgba(211,213,212,0.30)';
const TEXT_1    = '#E8ECF4';
const TEXT_2    = '#6B7280';

export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: DEEP,
  },
  safeArea: {
    flex: 1,
  },

  // ── Header ──
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: SURFACE,
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
  },
  backBtn: {
    width: 40,
    alignItems: 'flex-start',
    justifyContent: 'center',
  },
  backArrow: {
    color: TEXT_1,
    fontSize: 34,
    lineHeight: 38,
    fontWeight: '200',
  },
  headerTitle: {
    flex: 1,
    color: TEXT_1,
    fontSize: 17,
    fontWeight: '700',
    textAlign: 'center',
  },
  headerSpacer: {
    width: 40,
  },

  // ── Scroll ──
  scroll: {
    paddingBottom: 20,
    gap: 16,
  },

  // ── Image preview (full-width, no side padding) ──
  imageOuter: {
    shadowColor: WHITESILVER,
    shadowOpacity: 0.25,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 4 },
    elevation: 10,
  },
  imageInner: {
    overflow: 'hidden',
    height: 380,
    backgroundColor: SURFACE,
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
    backgroundColor: SURFACE,
    borderWidth: 1,
    borderColor: BORDER_MD,
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
    borderTopColor: BORDER,
  },
  checkMark: {
    fontSize: 16,
  },
  checkText: {
    flex: 1,
    color: TEXT_2,
    fontSize: 13,
    lineHeight: 18,
  },

  // ── Health note section ──
  noteSection: {
    gap: 10,
    paddingHorizontal: 20,
    paddingVertical: 14,
  },
  noteSectionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  noteSectionLabel: {
    color: TEXT_1,
    fontSize: 15,
    fontWeight: '700',
  },
  editBtn: {
    color: WHITESILVER,
    fontSize: 13,
    fontWeight: '600',
  },
  noteCard: {
    backgroundColor: SURFACE2,
    borderWidth: 1,
    borderColor: BORDER_MD,
    borderRadius: 14,
    padding: 14,
    gap: 8,
  },
  noteCardText: {
    color: TEXT_1,
    fontSize: 14,
    lineHeight: 21,
  },
  editHint: {
    color: TEXT_2,
    fontSize: 11,
  },
  noNoteRow: {
    backgroundColor: SURFACE,
    borderWidth: 1,
    borderColor: BORDER,
    borderRadius: 14,
    padding: 14,
  },
  noNoteText: {
    color: TEXT_2,
    fontSize: 14,
  },

  // ── Bottom buttons ──
  buttons: {
    flexDirection: 'row',
    padding: 20,
    paddingTop: 14,
    gap: 14,
    borderTopWidth: 1,
    borderTopColor: BORDER,
    backgroundColor: SURFACE,
    alignItems: 'center',
  },
  retakeBtn: {
    width: 56,
    height: 56,
    borderRadius: 28,
    borderWidth: 1.5,
    borderColor: WHITESILVER_BDR,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(211,213,212,0.08)',
  },
  retakeIcon: {
    width: 56,
    height: 56,
    resizeMode: 'contain',
    tintColor: WHITESILVER,
  },
  sendWrapper: {
    flex: 1,
  },
  sendBtn: {
    flex: 1,
    height: 54,
    borderRadius: 28,
    borderWidth: 1.5,
    borderColor: WHITESILVER_BDR,
    backgroundColor: 'rgba(211,213,212,0.08)',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  shimmerOverlay: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: 120,
    overflow: 'hidden',
  },
  sendBtnText: {
    color: WHITESILVER,
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
    backgroundColor: SURFACE,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    borderWidth: 1,
    borderBottomWidth: 0,
    borderColor: BORDER_MD,
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
    color: TEXT_1,
    fontSize: 18,
    fontWeight: '700',
  },
  modalSubtitle: {
    color: TEXT_2,
    fontSize: 13,
    lineHeight: 19,
    marginTop: -4,
  },
  modalInput: {
    backgroundColor: SURFACE2,
    borderWidth: 1,
    borderColor: BORDER_MD,
    borderRadius: 14,
    padding: 14,
    color: TEXT_1,
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
