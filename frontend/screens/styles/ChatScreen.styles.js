import { StyleSheet } from 'react-native';
import { colors } from '../../constants/colors';

// ─── Analysis pipeline verdict colors ────────────────────────────────────────
export const V_BG = {
  safe:    'rgba(0,179,65,0.07)',
  caution: 'rgba(230,168,23,0.07)',
  avoid:   'rgba(229,57,53,0.07)',
};

export const V_BORDER = {
  safe:    'rgba(0,179,65,0.22)',
  caution: 'rgba(230,168,23,0.22)',
  avoid:   'rgba(229,57,53,0.22)',
};

// ─── Main screen styles ───────────────────────────────────────────────────────
export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },

  // ── Header ──
  header: {
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingBottom: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    backgroundColor: 'rgba(10,10,26,0.92)',
  },
  headerTitle: {
    color: colors.textPrimary,
    fontSize: 17,
    fontWeight: '700',
  },
  headerSub: {
    color: colors.textSecondary,
    fontSize: 11,
    marginTop: 2,
  },
  headerBackBtn: {
  position: 'absolute',
  left: 16,
  bottom: 12,
  },
  headerBackText: {
  color: colors.textPrimary,
  fontSize: 32,
  lineHeight: 32,
  },

  // ── Messages ──
  messagesScroll: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    gap: 16,
    paddingBottom: 8,
  },
  messagesContentEmpty: {
    flex: 1,
  },

  // ── Empty state ──
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    gap: 12,
  },
  emptyIconBox: {
    width: 72,
    height: 72,
    borderRadius: 20,
    backgroundColor: 'rgba(122,60,247,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(122,60,247,0.3)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  emptyIconText: { fontSize: 36 },
  emptyTitle: {
    color: colors.textPrimary,
    fontSize: 20,
    fontWeight: '700',
    textAlign: 'center',
  },
  emptyHint: {
    color: colors.textSecondary,
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 20,
  },

  // ── Message rows ──
  msgRowUser: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  msgRowAI: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },

  // ── AI avatar ──
  aiAvatar: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: 'rgba(122,60,247,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(122,60,247,0.3)',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    marginTop: 4,
  },
  aiAvatarText: { fontSize: 16 },

  // ── Bubbles ──
  msgBubbleUser: {
    maxWidth: '78%',
    backgroundColor: colors.primary,
    borderRadius: 20,
    borderBottomRightRadius: 4,
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  msgTextUser: {
    color: '#FFFFFF',
    fontSize: 15,
    lineHeight: 22,
  },
  msgBubbleAI: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.09)',
    borderRadius: 20,
    borderBottomLeftRadius: 4,
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  msgTextAI: {
    color: colors.textPrimary,
    fontSize: 15,
    lineHeight: 24,
  },

  // ── Image in user bubble ──
  msgImage: {
    width: '100%',
    height: 160,
    borderRadius: 12,
    resizeMode: 'cover',
  },

  // ── Inline result card ──
  resultCard: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 20,
    borderBottomLeftRadius: 4,
    padding: 14,
    gap: 12,
  },

  // ── Bouncing dots ──
  dotsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 99,
    backgroundColor: colors.primary,
    opacity: 0.8,
  },

  // ── Claude-style thinking panel ──
  thinkingPanel: {
    flex: 1,
    backgroundColor: 'rgba(122,60,247,0.06)',
    borderWidth: 1,
    borderColor: 'rgba(122,60,247,0.22)',
    borderRadius: 20,
    borderBottomLeftRadius: 4,
    overflow: 'hidden',
  },
  thinkingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  thinkingTitle: {
    flex: 1,
    color: colors.textSecondary,
    fontSize: 13,
    fontStyle: 'italic',
    fontWeight: '500',
  },
  thinkingChevron: {
    color: colors.textSecondary,
    fontSize: 16,
    lineHeight: 20,
  },

  // ── Stage list ──
  stageList: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(122,60,247,0.18)',
  },
  stageRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  stageRowBorder: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.05)',
  },

  // Status circle
  stageCircle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  stageCircleDone: {
    backgroundColor: 'rgba(0,179,65,0.15)',
    borderColor: 'rgba(0,179,65,0.3)',
  },
  stageCircleActive: {
    backgroundColor: 'rgba(122,60,247,0.2)',
    borderColor: 'rgba(122,60,247,0.45)',
  },
  stageCircleText: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.25)',
  },
  stageCircleTextDone: {
    color: '#00B341',
    fontWeight: '700',
  },
  stageCircleTextActive: {
    color: colors.primary,
  },

  // Stage label + detail
  stageLabel: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.25)',
    fontWeight: '500',
  },
  stageLabelDone: {
    color: 'rgba(0,179,65,0.65)',
  },
  stageLabelActive: {
    color: colors.textPrimary,
    fontWeight: '700',
  },
  stageDetail: {
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: 2,
    lineHeight: 15,
  },

  // ── Suggestion chips ──
  chipsScroll: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: 10,
    paddingBottom: 8,
    flexGrow: 0,
    flexShrink: 0,
  },
  chipsRow: {
    paddingHorizontal: 16,
    gap: 8,
  },
  chip: {
    backgroundColor: 'rgba(122,60,247,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(122,60,247,0.35)',
    borderRadius: 99,
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  chipText: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: '500',
  },

  // ── Attachment preview strip ──
  attachmentStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    backgroundColor: 'rgba(10,10,26,0.96)',
  },
  attachmentThumb: {
    width: 56,
    height: 56,
    borderRadius: 10,
    resizeMode: 'cover',
  },
  attachmentRemove: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: 'rgba(255,255,255,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  attachmentRemoveText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
  },
  attachmentHint: {
    flex: 1,
    color: colors.textSecondary,
    fontSize: 12,
  },

  // ── Input bar ──
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
    paddingHorizontal: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: 'rgba(10,10,26,0.96)',
  },
  iconBtn: {
    width: 40,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconBtnText: {
    color: colors.textSecondary,
    fontSize: 22,
  },
  textInput: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    backgroundColor: 'rgba(255,255,255,0.07)',
    borderRadius: 22,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.12)',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 12,
    color: colors.textPrimary,
    fontSize: 15,
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendBtnDisabled: {
    opacity: 0.3,
  },
  sendArrow: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '700',
    lineHeight: 24,
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
  },
  type: {
    color: colors.textSecondary,
    fontSize: 11,
    marginTop: 2,
  },
  confRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  confLabel: {
    color: colors.textSecondary,
    fontSize: 12,
    width: 72,
  },
  confBarBg: {
    flex: 1,
    height: 5,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 3,
    overflow: 'hidden',
  },
  confBarFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 3,
  },
  confPct: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: '700',
    width: 36,
    textAlign: 'right',
  },
  summary: {
    color: colors.textSecondary,
    fontSize: 13,
    lineHeight: 20,
  },
  fullAnalysisBtn: {
    alignSelf: 'stretch',
    paddingVertical: 10,
    paddingHorizontal: 18,
    backgroundColor: 'rgba(122,60,247,0.12)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(122,60,247,0.3)',
    alignItems: 'center',
  },
  fullAnalysisBtnText: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: '700',
  },
});