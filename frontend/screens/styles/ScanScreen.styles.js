import { StyleSheet } from 'react-native';
import { colors } from '../../constants/colors';

// ─── Enterprise dark palette (mirrors ChatScreen) ────────────────────────────
const DEEP      = '#0d131a';
const SURFACE   = '#141c26';
const SURFACE2  = '#333740';
const BORDER    = 'rgba(255,255,255,0.07)';
const BORDER_MD = 'rgba(255,255,255,0.11)';
const CYAN      = '#d3d5d4';
const CYAN_DIM  = 'rgba(211,213,212,0.15)';
const CYAN_BDR  = 'rgba(211,213,212,0.30)';
const TEXT_1    = '#E8ECF4';
const TEXT_2    = '#6B7280';

// ─── Styles ───────────────────────────────────────────────────────────────────
export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: DEEP,
  },
  safeOverlay: {
    flex: 1,
    justifyContent: 'space-between',
  },

  // ── Header ──
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: 'transparent',
  },
  headerBtn: {
    width: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backArrow: {
    color: TEXT_1,
    fontSize: 34,
    lineHeight: 38,
    fontWeight: '200',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  appName: {
    color: TEXT_1,
    fontSize: 20,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  subtitle: {
    color: TEXT_2,
    fontSize: 12,
    marginTop: 2,
  },
  lastScanBtn: {
    width: 44,
    alignItems: 'flex-end',
  },
  lastScanText: {
    color: CYAN,
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'right',
  },

  // ── Capture guide frame ──
  frameArea: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 14,
  },
  captureFrame: {
    width: '82%',
    aspectRatio: 0.75,
    backgroundColor: 'transparent',
  },
  corner: {
    position: 'absolute',
    width: 32,
    height: 32,
    borderColor: '#FFFFFF',
    borderWidth: 3,
  },
  cornerTL: { top: 0, left: 0, borderBottomWidth: 0, borderRightWidth: 0, borderTopLeftRadius: 10 },
  cornerTR: { top: 0, right: 0, borderBottomWidth: 0, borderLeftWidth: 0, borderTopRightRadius: 10 },
  cornerBL: { bottom: 0, left: 0, borderTopWidth: 0, borderRightWidth: 0, borderBottomLeftRadius: 10 },
  cornerBR: { bottom: 0, right: 0, borderTopWidth: 0, borderLeftWidth: 0, borderBottomRightRadius: 10 },
  frameHint: {
    color: 'rgba(255,255,255,0.55)',
    fontSize: 12,
    letterSpacing: 0.3,
  },

  // ── Shutter row ──
  shutterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 40,
    paddingVertical: 32,
    backgroundColor: 'transparent',
  },
  galleryBtn: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: 'rgba(255,255,255,0.22)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  galleryIcon: {
    width: 40,
    height: 40,
    resizeMode: 'contain',
    tintColor: '#FFFFFF',
  },
  galleryBtnActive: {
    backgroundColor: 'rgba(255,220,80,0.35)',
  },
  torchIconActive: {
    width: 40,
    height: 40,
    resizeMode: 'contain',
    tintColor: '#FFE050',
  },
  shutterBtn: {
    width: 78,
    height: 78,
    borderRadius: 39,
    backgroundColor: 'rgba(255,255,255,0.25)',
    borderWidth: 3,
    borderColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  shutterInner: {
    width: 62,
    height: 62,
    borderRadius: 31,
    backgroundColor: '#FFFFFF',
  },

  // ── Permission screen ──
  permContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
    gap: 16,
  },
  permEmoji: {
    fontSize: 64,
    marginBottom: 4,
  },
  permTitle: {
    color: TEXT_1,
    fontSize: 22,
    fontWeight: '700',
    textAlign: 'center',
  },
  permBody: {
    color: TEXT_2,
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
  },
  permBtn: {
    width: '100%',
    marginTop: 8,
    borderRadius: 16,
    overflow: 'hidden',
  },
  permBtnInner: {
    paddingVertical: 16,
    alignItems: 'center',
    borderRadius: 16,
  },
  permBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  permDenied: {
    color: colors.warning,
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 20,
    marginTop: 8,
  },
});
