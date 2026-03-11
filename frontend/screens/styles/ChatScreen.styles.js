import { StyleSheet } from 'react-native';
import { colors } from '../../constants/colors';

// ─── Verdict tints (result card backgrounds / borders) ───────────────────────
export const V_BG = {
  safe:    'rgba(0,179,65,0.08)',
  caution: 'rgba(230,168,23,0.08)',
  avoid:   'rgba(229,57,53,0.08)',
};

export const V_BORDER = {
  safe:    'rgba(0,179,65,0.25)',
  caution: 'rgba(230,168,23,0.25)',
  avoid:   'rgba(229,57,53,0.25)',
};

// ─── Enterprise dark palette ───────────────────────────────────────────────
const DEEP        = '#0d131a';           // near-black base
const SURFACE     = '#141c26';           // elevated surface
const SURFACE2    = '#333740';           // card/panel surface
const BORDER      = 'rgba(255,255,255,0.07)';
const BORDER_MED  = 'rgba(255,255,255,0.11)';
const WHITESILVER        = '#d3d5d4';           // silver accent
const WHITESILVER_DIM    = 'rgba(211,213,212,0.18)';
const WHITESILVER_BORDER = 'rgba(211,213,212,0.30)';
const TEAL        = '#00E5C8';           // secondary teal success
const AMBER       = '#F0A500';           // amber warning / accent
const ONLINE      = '#00E5A0';           // live status
const TEXT_1      = '#E8ECF4';           // primary text
const TEXT_2      = '#6B7280';           // secondary / muted
const TEXT_3      = 'rgba(232,236,244,0.45)'; // tertiary

// ─── Main screen styles ───────────────────────────────────────────────────────
export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: DEEP,
  },

  // ── Header ────────────────────────────────────────────────────────────────
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
    backgroundColor: SURFACE,
    gap: 8,
  },
  headerBackBtn: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: SURFACE2,
    borderWidth: 1,
    borderColor: BORDER_MED,
    flexShrink: 0,
  },
  headerBackText: {
    color: TEXT_1,
    fontSize: 26,
    lineHeight: 30,
    fontWeight: '300',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
    gap: 2,
  },
  headerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
  },
  headerTitle: {
    color: TEXT_1,
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.4,
  },
  headerDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: ONLINE,
    shadowColor: ONLINE,
    shadowOpacity: 1,
    shadowRadius: 5,
    shadowOffset: { width: 0, height: 0 },
  },
  headerSub: {
    color: TEXT_2,
    fontSize: 11,
    letterSpacing: 0.2,
  },
  headerScanBtn: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: WHITESILVER,
    borderWidth: 1,
    borderColor: WHITESILVER_BORDER,
    flexShrink: 0,
  },
  headerScanIcon: {
    fontSize: 18,
  },
  // Burger menu button (3 bars)
  burgerWrap: {
    gap: 4,
    alignItems: 'flex-end',
    justifyContent: 'center',
    paddingHorizontal: 2,
  },
  burgerBar: {
    width: 18,
    height: 2,
    borderRadius: 2,
    backgroundColor: TEXT_1,
  },

  // ── Messages ──────────────────────────────────────────────────────────────
  messagesScroll: {
    flex: 1,
  },
  messagesContent: {
    padding: 20,
    gap: 18,
    paddingBottom: 12,
  },
  messagesContentEmpty: {
    flex: 1,
  },

  // ── Empty state ───────────────────────────────────────────────────────────
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 28,
    gap: 14,
  },
  emptyLogo: {
    width: 96,
    height: 96,
    borderRadius: 28,
    marginBottom: 4,
    shadowColor: WHITESILVER,
    shadowOpacity: 0.35,
    shadowRadius: 28,
    shadowOffset: { width: 0, height: 0 },
    elevation: 12,
  },
  emptyTitle: {
    color: TEXT_1,
    fontSize: 23,
    fontWeight: '800',
    textAlign: 'center',
    letterSpacing: 0.3,
  },
  emptyHint: {
    color: TEXT_2,
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
  },
  // Feature pills row
  emptyFeatures: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 8,
    marginTop: 4,
  },
  featurePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: SURFACE2,
    borderWidth: 1,
    borderColor: BORDER_MED,
    borderRadius: 99,
    paddingVertical: 7,
    paddingHorizontal: 13,
  },
  featurePillIcon: { fontSize: 13 },
  featurePillText: {
    color: TEXT_3,
    fontSize: 12,
    fontWeight: '500',
  },

  // ── Message rows ──────────────────────────────────────────────────────────
  msgRowUser: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  msgRowAI: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },

  // ── AI avatar ─────────────────────────────────────────────────────────────
  aiAvatar: {
    width: 34,
    height: 34,
    borderRadius: 11,
    backgroundColor: WHITESILVER,
    borderWidth: 1,
    borderColor: WHITESILVER_BORDER,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    marginTop: 2,
    shadowColor: WHITESILVER,
    shadowOpacity: 0.25,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 0 },
    elevation: 4,
  },
  aiAvatarText: { fontSize: 16 },
  aiAvatarImg: {
    width: 34,
    height: 34,
    borderRadius: 11,
  },

  // ── User bubble ───────────────────────────────────────────────────────────
  msgBubbleUser: {
    maxWidth: '78%',
    backgroundColor: WHITESILVER,
    borderRadius: 22,
    borderBottomRightRadius: 4,
    paddingVertical: 12,
    paddingHorizontal: 18,
    shadowColor: WHITESILVER,
    shadowOpacity: 0.35,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
  },
  msgTextUser: {
    color: '#040810',
    fontSize: 15,
    lineHeight: 23,
    fontWeight: '600',
  },

  // ── AI bubble ─────────────────────────────────────────────────────────────
  msgBubbleAI: {
    flex: 1,
    backgroundColor: SURFACE2,
    borderWidth: 1,
    borderColor: BORDER_MED,
    borderRadius: 22,
    borderBottomLeftRadius: 4,
    paddingVertical: 14,
    paddingHorizontal: 18,
  },
  msgTextAI: {
    color: TEXT_1,
    fontSize: 15,
    lineHeight: 25,
  },

  // ── Image message bubble ──────────────────────────────────────────
  msgBubbleImage: {
    width: '65%',
    padding: 0,
    overflow: 'hidden',
  },
  msgImage: {
    width: '100%',
    aspectRatio: 4 / 3,
    borderRadius: 18,
  },

  // ── Inline result card ────────────────────────────────────────────────────
  resultCard: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 22,
    borderBottomLeftRadius: 4,
    padding: 16,
    gap: 12,
  },

  // ── Bouncing dots ─────────────────────────────────────────────────────────
  dotsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 99,
    backgroundColor: WHITESILVER,
    opacity: 0.9,
  },

  // ── Thinking / analyzing panel ────────────────────────────────────────────
  thinkingPanel: {
    flex: 1,
    backgroundColor: SURFACE2,
    borderWidth: 1,
    borderColor: BORDER_MED,
    borderRadius: 22,
    borderBottomLeftRadius: 4,
    overflow: 'hidden',
  },
  thinkingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 16,
    paddingVertical: 13,
  },
  thinkingTitle: {
    flex: 1,
    color: TEXT_3,
    fontSize: 13,
    fontStyle: 'italic',
    fontWeight: '500',
    letterSpacing: 0.2,
  },
  thinkingChevron: {
    color: TEXT_2,
    fontSize: 16,
    lineHeight: 20,
  },

  // ── Stage list ────────────────────────────────────────────────────────────
  stageList: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: BORDER,
  },
  stageRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 11,
  },
  stageRowBorder: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: BORDER,
  },
  stageCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: SURFACE2,
    borderWidth: 1,
    borderColor: BORDER_MED,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  stageCircleDone: {
    backgroundColor: 'rgba(0,229,200,0.10)',
    borderColor: 'rgba(0,229,200,0.28)',
  },
  stageCircleActive: {
    backgroundColor: WHITESILVER_DIM,
    borderColor: WHITESILVER_BORDER,
    shadowColor: WHITESILVER,
    shadowOpacity: 0.55,
    shadowRadius: 7,
    shadowOffset: { width: 0, height: 0 },
    elevation: 3,
  },
  stageCircleText: {
    fontSize: 11,
    color: TEXT_2,
  },
  stageCircleTextDone: {
    color: TEAL,
    fontWeight: '700',
  },
  stageCircleTextActive: {
    color: WHITESILVER,
  },
  stageLabel: {
    fontSize: 13,
    color: TEXT_2,
    fontWeight: '500',
  },
  stageLabelDone: {
    color: 'rgba(0,229,200,0.65)',
  },
  stageLabelActive: {
    color: TEXT_1,
    fontWeight: '700',
  },
  stageDetail: {
    fontSize: 11,
    color: TEXT_2,
    marginTop: 2,
    lineHeight: 16,
  },

  // ── Suggestion chips ──────────────────────────────────────────────────────
  chipsScroll: {
    paddingTop: 12,
    paddingBottom: 10,
    flexGrow: 0,
    flexShrink: 0,
  },
  chipsRow: {
    paddingHorizontal: 16,
    gap: 8,
  },
  chip: {
    backgroundColor: SURFACE2,
    borderWidth: 1,
    borderColor: BORDER_MED,
    borderRadius: 99,
    paddingVertical: 9,
    paddingHorizontal: 18,
  },
  chipText: {
    color: TEXT_1,
    fontSize: 13,
    fontWeight: '500',
  },

  // ── Attachment preview strip ──────────────────────────────────────────────
  attachmentStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: BORDER,
    backgroundColor: SURFACE,
  },
  attachmentThumb: {
    width: 52,
    height: 52,
    borderRadius: 12,
    resizeMode: 'cover',
  },
  attachmentRemove: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: 'rgba(255,255,255,0.14)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  attachmentRemoveText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
  },
  attachmentHint: {
    flex: 1,
    color: TEXT_2,
    fontSize: 12,
    lineHeight: 18,
  },

  // ── Input bar ─────────────────────────────────────────────────────────────
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 10,
    paddingHorizontal: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: BORDER,
    backgroundColor: SURFACE,
  },
  iconBtn: {
    width: 42,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 13,
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  iconBtnText: {
    color: colors.textSecondary,
    fontSize: 20,
  },

  // ── + button ──────────────────────────────────────────────────────────────
  plusBtn: {
    width: 42,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 13,
    backgroundColor: SURFACE2,
    borderWidth: 1,
    borderColor: BORDER_MED,
  },
  plusBtnIcon: {
    width: 40,
    height: 40,
    resizeMode: 'contain',
  },

  // ── Pop-up attachment menu ────────────────────────────────────────────────
  bottomArea: {
    flexShrink: 0,
  },
  popMenu: {
    position: 'absolute',
    bottom: 100,
    left: 14,
    zIndex: 20,
    backgroundColor: '#141428',
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.10)',
    overflow: 'hidden',
    minWidth: 218,
    shadowColor: '#000',
    shadowOpacity: 0.55,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 8 },
    elevation: 18,
  },
  popMenuDivider: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: 'rgba(255,255,255,0.07)',
    marginHorizontal: 14,
  },
  popMenuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 13,
    paddingVertical: 14,
    paddingHorizontal: 18,
  },
  popMenuItemImg: {
    width: 70,
    height: 40,
    resizeMode: 'contain',
  },
  popMenuItemLabel: {
    color: colors.textPrimary,
    fontSize: 14,
    fontWeight: '500',
  },
  popMenuItemLabelDanger: {
    color: colors.danger,
    fontSize: 14,
    fontWeight: '500',
  },

  textInput: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    backgroundColor: SURFACE2,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: BORDER_MED,
    paddingHorizontal: 18,
    paddingTop: 12,
    paddingBottom: 12,
    color: TEXT_1,
    fontSize: 15,
    lineHeight: 20,
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: WHITESILVER,
    shadowOpacity: 0.4,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 2 },
    elevation: 5,
  },
  sendBtnDisabled: {
    opacity: 0.24,
  },
  sendIcon: {
    width: 75,
    height: 90,
    resizeMode: 'contain',
  },
});

// ─── Result card inner styles ─────────────────────────────────────────────────
export const rs = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  product: {
    color: colors.textPrimary,
    fontSize: 16,
    fontWeight: '800',
    lineHeight: 22,
    letterSpacing: 0.2,
  },
  type: {
    color: colors.textSecondary,
    fontSize: 11,
    marginTop: 3,
    letterSpacing: 0.3,
  },
  confRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  confLabel: {
    color: colors.textSecondary,
    fontSize: 10,
    width: 70,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    fontWeight: '600',
  },
  confBarBg: {
    flex: 1,
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  confBarFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 2,
  },
  confPct: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '700',
    width: 36,
    textAlign: 'right',
  },
  summary: {
    color: 'rgba(180,178,210,0.85)',
    fontSize: 13,
    lineHeight: 21,
  },
  fullAnalysisBtn: {
    alignSelf: 'stretch',
    paddingVertical: 11,
    paddingHorizontal: 18,
    backgroundColor: 'rgba(122,60,247,0.10)',
    borderRadius: 13,
    borderWidth: 1,
    borderColor: 'rgba(122,60,247,0.28)',
    alignItems: 'center',
  },
  fullAnalysisBtnText: {
    color: 'rgba(188,160,255,0.95)',
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
});