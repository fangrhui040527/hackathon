import { StyleSheet } from 'react-native';
import { colors } from '../../constants/colors';

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
  },

  // ── Health-note confirmation banner ──
  banner: {
    backgroundColor: '#0A2E1A',
    borderWidth: 1,
    borderColor: '#00B34133',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  bannerText: {
    color: colors.success,
    fontSize: 13,
    fontWeight: '600',
    lineHeight: 18,
  },

  // ── Center pulsing icon ──
  centerSection: {
    alignItems: 'center',
    paddingVertical: 8,
    gap: 12,
  },
  iconBox: {
    width: 88,
    height: 88,
    borderRadius: 24,
    backgroundColor: 'rgba(122,60,247,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(122,60,247,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.primary,
    shadowOpacity: 0.4,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 0 },
    elevation: 8,
  },
  iconEmoji: {
    fontSize: 42,
  },
  stageLabel: {
    color: colors.textPrimary,
    fontSize: 20,
    fontWeight: '700',
    textAlign: 'center',
  },
  stageSubtitle: {
    color: colors.textSecondary,
    fontSize: 13,
  },

  // ── Step list ──
  stepList: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    overflow: 'hidden',
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 13,
    paddingHorizontal: 16,
    gap: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  stepCircle: {
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  stepCircleGlow: {
    shadowColor: colors.primary,
    shadowOpacity: 0.7,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 0 },
    elevation: 6,
  },
  stepCircleIcon: {
    fontSize: 16,
  },
  stepLabel: {
    flex: 1,
    fontSize: 13,
    fontWeight: '500',
  },

  // ── Bounce dots ──
  bounceDots: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingRight: 2,
  },
  bounceDot: {
    width: 5,
    height: 5,
    borderRadius: 99,
    backgroundColor: colors.primary,
  },
});
