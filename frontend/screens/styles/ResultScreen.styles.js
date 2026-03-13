import { StyleSheet } from 'react-native';
import { colors } from '../../constants/colors';

// ─── Enterprise dark palette ──────────────────────────────────────────────────
const DEEP      = '#0d131a';
const SURFACE   = '#141c26';
const SURFACE2  = '#1e2837';
const BORDER    = 'rgba(255,255,255,0.07)';
const BORDER_MD = 'rgba(255,255,255,0.12)';
const SILVER    = '#d3d5d4';
const TEXT_1    = '#E8ECF4';
const TEXT_2    = '#6B7280';
const TEXT_3    = 'rgba(232,236,244,0.45)';

// ─── Verdict config ───────────────────────────────────────────────────────────
export const VERDICT_CONFIG = {
  safe: {
    bg: 'rgba(0,179,65,0.08)',
    border: 'rgba(0,179,65,0.30)',
    glowColor: '#00B341',
    emoji: '✅',
    headline: 'Generally safe to consume',
    label: 'SAFE',
  },
  caution: {
    bg: 'rgba(230,168,23,0.08)',
    border: 'rgba(230,168,23,0.30)',
    glowColor: '#E6A817',
    emoji: '⚠️',
    headline: 'Consume with caution',
    label: 'CAUTION',
  },
  avoid: {
    bg: 'rgba(229,57,53,0.08)',
    border: 'rgba(229,57,53,0.30)',
    glowColor: '#E53935',
    emoji: '🚫',
    headline: 'Not recommended for regular consumption',
    label: 'AVOID',
  },
};

// ─── Styles ───────────────────────────────────────────────────────────────────
export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: DEEP,
  },
  safeArea: {
    flex: 1,
  },
  scroll: {
    padding: 18,
    gap: 14,
    paddingBottom: 48,
  },

  // ── Header ──
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
    backgroundColor: SURFACE,
  },
  backBtn: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: SURFACE2,
    borderWidth: 1,
    borderColor: BORDER_MD,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backArrow: {
    color: TEXT_1,
    fontSize: 28,
    lineHeight: 32,
    fontWeight: '300',
    marginTop: -2,
  },
  headerTitle: {
    flex: 1,
    color: TEXT_1,
    fontSize: 15,
    fontWeight: '700',
    textAlign: 'center',
    letterSpacing: 0.3,
  },
  headerSpacer: {
    width: 38,
  },

  // ── Empty state ──
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyText: {
    color: TEXT_2,
    fontSize: 15,
  },

  // ── Section heading with left-bar ──
  sectionHeadRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    marginBottom: 2,
  },
  sectionHeadBar: {
    width: 3,
    minHeight: 20,
    borderRadius: 2,
    backgroundColor: SILVER,
    marginTop: 2,
  },
  sectionTitle: {
    color: TEXT_1,
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 0.2,
  },
  sectionSubtitle: {
    color: TEXT_2,
    fontSize: 12,
    marginTop: 2,
    lineHeight: 17,
  },
  section: {
    gap: 10,
  },

  // ── B: Product card ──
  productCard: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1,
    borderColor: BORDER_MD,
    borderRadius: 20,
    overflow: 'hidden',
    gap: 10,
    paddingBottom: 16,
  },
  productCardGradient: {
    position: 'absolute',
    top: 0, left: 0, right: 0,
    height: 60,
    borderRadius: 20,
  },
  productCardTop: {
    flexDirection: 'row',
    justifyContent: 'flex-start',
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  productScanBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(211,213,212,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(211,213,212,0.28)',
    borderRadius: 99,
    paddingHorizontal: 10,
    paddingVertical: 4,
    gap: 5,
  },
  productScanBadgeText: {
    color: SILVER,
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  productName: {
    color: TEXT_1,
    fontSize: 22,
    fontWeight: '800',
    letterSpacing: 0.2,
    paddingHorizontal: 16,
    lineHeight: 28,
  },
  productTagsRow: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 16,
    flexWrap: 'wrap',
  },
  productTag: {
    backgroundColor: 'rgba(255,255,255,0.07)',
    borderWidth: 1,
    borderColor: BORDER_MD,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  productTagText: {
    color: TEXT_2,
    fontSize: 12,
    fontWeight: '500',
  },
  nutriDivider: {
    height: 1,
    backgroundColor: BORDER,
    marginHorizontal: 16,
  },
  nutriGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 12,
    gap: 8,
  },
  nutriCell: {
    width: '22%',
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderWidth: 1,
    borderColor: BORDER,
    borderRadius: 12,
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 4,
    gap: 3,
  },
  nutriIcon: {
    fontSize: 18,
  },
  nutriValue: {
    color: TEXT_1,
    fontSize: 11,
    fontWeight: '800',
    textAlign: 'center',
  },
  nutriLabel: {
    color: TEXT_3,
    fontSize: 9,
    fontWeight: '600',
    textAlign: 'center',
    letterSpacing: 0.3,
  },

  // ── C: Verdict card ──
  verdictCard: {
    borderWidth: 1.5,
    borderRadius: 22,
    gap: 16,
    paddingBottom: 20,
  },
  verdictTopGlow: {
    height: 80,
    position: 'absolute',
    top: 0, left: 0, right: 0,
  },
  verdictHero: {
    alignItems: 'center',
    gap: 10,
    paddingTop: 28,
    paddingHorizontal: 20,
  },
  verdictEmojiRing: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
    shadowOpacity: 0.5,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 0 },
    elevation: 8,
  },
  verdictHeroEmoji: {
    fontSize: 40,
  },
  verdictLabelPill: {
    borderWidth: 1,
    borderRadius: 99,
    paddingHorizontal: 16,
    paddingVertical: 5,
  },
  verdictLabelText: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 2,
  },
  verdictHeadline: {
    color: TEXT_1,
    fontSize: 17,
    fontWeight: '800',
    textAlign: 'center',
    lineHeight: 24,
  },
  verdictGradientDivider: {
    height: 1,
    marginHorizontal: 20,
    marginTop: -4,
  },
  verdictNoteChip: {
    backgroundColor: 'rgba(195,166,255,0.10)',
    borderWidth: 1,
    borderColor: 'rgba(195,166,255,0.28)',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginHorizontal: 20,
  },
  verdictNoteText: {
    color: '#C3A6FF',
    fontSize: 12,
    lineHeight: 18,
  },
  verdictSummary: {
    color: TEXT_2,
    fontSize: 14,
    lineHeight: 24,
    paddingHorizontal: 20,
  },
  confidenceWrapper: {
    paddingHorizontal: 20,
    paddingBottom: 4,
  },

  // ── Columns ──
  columnsRow: {
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 20,
  },
  column: {
    flex: 1,
    borderRadius: 14,
    padding: 12,
    gap: 7,
  },
  columnOk: {
    backgroundColor: 'rgba(0,179,65,0.07)',
    borderWidth: 1,
    borderColor: 'rgba(0,179,65,0.18)',
  },
  columnAvoid: {
    backgroundColor: 'rgba(229,57,53,0.07)',
    borderWidth: 1,
    borderColor: 'rgba(229,57,53,0.18)',
  },
  columnTitle: {
    color: TEXT_2,
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  columnItemRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 7,
  },
  columnDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 5,
    flexShrink: 0,
  },
  columnItem: {
    color: TEXT_2,
    fontSize: 12,
    lineHeight: 18,
    flex: 1,
  },
  columnItemMatch: {
    color: '#E53935',
    fontWeight: '700',
  },

  // ── D: Fun fact cards ──
  factCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1,
    borderColor: BORDER_MD,
    borderRadius: 16,
    padding: 14,
    gap: 12,
  },
  factNumber: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: 'rgba(211,213,212,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(211,213,212,0.25)',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  factNumberText: {
    color: SILVER,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  factText: {
    color: TEXT_1,
    fontSize: 13,
    lineHeight: 20,
    flex: 1,
  },

  // ── E: Team row ──
  teamRow: {
    flexDirection: 'row',
    justifyContent: 'space-evenly',
    alignItems: 'center',
  },
  teamAvatar: {
    width: 44,
    height: 44,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  teamAvatarEmoji: {
    fontSize: 22,
  },

  // ── Full-screen image modal ──
  imageModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.92)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  imageModalImg: {
    width: '92%',
    height: '72%',
    borderRadius: 16,
  },
  imageModalClose: {
    position: 'absolute',
    top: 52,
    right: 20,
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  imageModalCloseText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

