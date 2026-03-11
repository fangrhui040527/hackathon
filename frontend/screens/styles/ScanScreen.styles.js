import { StyleSheet } from 'react-native';
import { colors } from '../../constants/colors';

// ─── Scanning frame constants ─────────────────────────────────────────────────
export const FRAME_SIZE    = 260;
export const CORNER_LEN    = 28;
export const CORNER_W      = 3;
export const BRACKET_COLOR = '#d3d5d4';    // silver to match enterprise theme

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
    backgroundColor: SURFACE,
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
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

  // ── Center / scanning frame ──
  centerSection: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  scanFrame: {
    width: FRAME_SIZE,
    height: FRAME_SIZE,
    overflow: 'hidden',
  },
  scanLine: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 2,
    backgroundColor: CYAN,
    shadowColor: CYAN,
    shadowOpacity: 1,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 0 },
  },
  frameHint: {
    color: 'rgba(255,255,255,0.45)',
    fontSize: 12,
  },

  // ── Corner brackets ──
  bracketWrap: {
    position: 'absolute',
    width: CORNER_LEN,
    height: CORNER_LEN,
  },
  bracketH: {
    position: 'absolute',
    width: CORNER_LEN,
    height: CORNER_W,
    backgroundColor: BRACKET_COLOR,
    borderRadius: 2,
  },
  bracketV: {
    position: 'absolute',
    width: CORNER_W,
    height: CORNER_LEN,
    backgroundColor: BRACKET_COLOR,
    borderRadius: 2,
  },

  // ── Bottom panel ──
  bottomPanel: {
    backgroundColor: SURFACE,
    borderTopWidth: 1,
    borderTopColor: BORDER,
    padding: 20,
    gap: 12,
  },
  // Side-by-side row
  bottomBtnsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  halfBtn: {
    flex: 1,
    height: 54,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  cameraBtnText: {
    color: '#040810',
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  cameraBtnIcon: {
    width: 40,
    height: 40,
    resizeMode: 'contain',
    tintColor: '#040810',
  },
  uploadBtn: {
    flex: 1,
    height: 54,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: CYAN_BDR,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
    backgroundColor: CYAN_DIM,
  },
  uploadBtnText: {
    color: CYAN,
    fontSize: 15,
    fontWeight: '600',
  },
  uploadBtnIcon: {
    width: 40,
    height: 40,
    resizeMode: 'contain',
    tintColor: CYAN,
  },
  tip: {
    color: TEXT_2,
    fontSize: 11,
    textAlign: 'center',
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
