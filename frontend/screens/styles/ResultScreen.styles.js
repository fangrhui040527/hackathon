import { StyleSheet } from 'react-native';
import { colors } from '../../constants/colors';

// ─── Verdict background / border tints (mirrors ChatScreen pattern) ───────────
export const VERDICT_CONFIG = {
  safe: {
    bg: '#051A0A', border: '#00B34144',
    emoji: '✅', headline: 'Generally safe to consume',
  },
  caution: {
    bg: '#1A1005', border: '#E6A81744',
    emoji: '⚠️',  headline: 'Consume with caution',
  },
  avoid: {
    bg: '#1A0505', border: '#E5393544',
    emoji: '🚫', headline: 'Not recommended for regular consumption',
  },
};

// ─── Styles ───────────────────────────────────────────────────────────────────
export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  safeArea: {
    flex: 1,
  },
  scroll: {
    padding: 20,
    gap: 16,
    paddingBottom: 40,
  },

  // ── Header ──
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    backgroundColor: 'rgba(10,10,26,0.92)',
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
    fontSize: 16,
    fontWeight: '700',
    textAlign: 'center',
  },
  headerSpacer: {
    width: 40,
  },

  // ── Empty state ──
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyText: {
    color: colors.textSecondary,
    fontSize: 15,
  },

  // ── Section headings ──
  sectionTitle: {
    color: colors.textPrimary,
    fontSize: 17,
    fontWeight: '700',
    marginBottom: 2,
  },
  sectionSubtitle: {
    color: colors.textSecondary,
    fontSize: 12,
    marginTop: -2,
    marginBottom: 4,
  },
  section: {
    gap: 10,
  },

  // ── B: Glassmorphism product card ──
  glassCard: {
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.10)',
    borderRadius: 20,
    padding: 18,
    gap: 6,
  },
  glassLabel: {
    color: colors.cyan,
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.5,
    textTransform: 'uppercase',
  },
  productName: {
    color: colors.textPrimary,
    fontSize: 22,
    fontWeight: '800',
    letterSpacing: 0.2,
  },
  productMeta: {
    color: colors.textSecondary,
    fontSize: 13,
  },
  pillsRow: {
    flexDirection: 'row',
    gap: 8,
    paddingTop: 4,
    paddingBottom: 2,
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 99,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  pillLabel: {
    color: colors.textSecondary,
    fontSize: 12,
  },
  pillValue: {
    color: colors.textPrimary,
    fontSize: 12,
    fontWeight: '700',
  },

  // ── C: Verdict banner ──
  verdictBanner: {
    borderWidth: 1,
    borderRadius: 20,
    padding: 18,
    gap: 14,
  },
  verdictHeadRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flexWrap: 'wrap',
  },
  verdictEmoji: {
    fontSize: 32,
  },
  verdictHeadline: {
    flex: 1,
    color: colors.textPrimary,
    fontSize: 18,
    fontWeight: '800',
    flexShrink: 1,
  },
  verdictNoteChip: {
    backgroundColor: '#1A0A2E',
    borderWidth: 1,
    borderColor: 'rgba(195,166,255,0.3)',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    alignSelf: 'flex-start',
  },
  verdictNoteText: {
    color: '#C3A6FF',
    fontSize: 12,
    lineHeight: 18,
  },
  verdictSummary: {
    color: colors.textSecondary,
    fontSize: 14,
    lineHeight: 24,
  },

  // ── Two-column ok_for / avoid_if ──
  columnsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  column: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderRadius: 12,
    padding: 12,
    gap: 6,
  },
  columnTitle: {
    color: colors.textSecondary,
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  columnItem: {
    color: colors.textSecondary,
    fontSize: 12,
    lineHeight: 18,
  },
  columnItemMatch: {
    color: colors.danger,
    fontWeight: '700',
  },

  // ── D: Fun fact cards ──
  factCard: {
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderRadius: 12,
    borderLeftWidth: 3,
    borderLeftColor: colors.primary,
    padding: 14,
  },
  factText: {
    color: colors.textPrimary,
    fontSize: 13,
    lineHeight: 20,
  },
});
