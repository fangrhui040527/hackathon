import React, { useRef } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '../constants/colors';
import { agents } from '../constants/agents';
import { useScan } from '../context/ScanContext';
import Background3D from '../components/Background3D';
import SubmissionCard from '../components/SubmissionCard';
import ConfidenceMeter from '../components/ConfidenceMeter';
import AgentCard from '../components/AgentCard';

// ─── Verdict display config ───────────────────────────────────────────────────
const VERDICT_CONFIG = {
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

// ─── Keyword match: highlight avoid_if items that match the health note ───────
function matchesHealthNote(item, healthNote) {
  if (!healthNote) return false;
  const note = healthNote.toLowerCase();
  return item
    .toLowerCase()
    .split(/\s+/)
    .some(w => w.replace(/[^a-z]/g, '').length > 4 && note.includes(w.replace(/[^a-z]/g, '')));
}

// ─── Section A helper: timestamp generated once ───────────────────────────────

// ─── Sub-components ───────────────────────────────────────────────────────────

// B) Product card (glassmorphism)
function ProductCard({ product, type, servingSize, nutrition = [] }) {
  return (
    <View style={styles.glassCard}>
      <Text style={styles.glassLabel}>SCANNED PRODUCT</Text>
      <Text style={styles.productName}>{product}</Text>

      {(type || servingSize) ? (
        <Text style={styles.productMeta}>
          {[type, servingSize].filter(Boolean).join('  ·  ')}
        </Text>
      ) : null}

      {nutrition.length > 0 && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.pillsRow}
          nestedScrollEnabled
        >
          {nutrition.map((item, i) => (
            <View key={i} style={styles.pill}>
              <Text style={styles.pillLabel}>{item.label}: </Text>
              <Text style={styles.pillValue}>{item.value}</Text>
            </View>
          ))}
        </ScrollView>
      )}
    </View>
  );
}

// C) Two-column ok_for / avoid_if
function ConditionColumn({ title, items, healthNote, isAvoid }) {
  return (
    <View style={styles.column}>
      <Text style={styles.columnTitle}>{title}</Text>
      {items.map((item, i) => {
        const matched = isAvoid && matchesHealthNote(item, healthNote);
        return (
          <Text
            key={i}
            style={[styles.columnItem, matched && styles.columnItemMatch]}
          >
            {item}{matched ? '  ← you' : ''}
          </Text>
        );
      })}
    </View>
  );
}

// C) Verdict banner
function VerdictBanner({ conclusion, healthNote }) {
  const {
    verdict = 'caution',
    summary = '',
    ok_for = [],
    avoid_if = [],
    confidence = 0,
  } = conclusion;

  const vc = VERDICT_CONFIG[verdict] ?? VERDICT_CONFIG.caution;

  return (
    <View style={[styles.verdictBanner, { backgroundColor: vc.bg, borderColor: vc.border }]}>
      {/* Verdict headline */}
      <View style={styles.verdictHeadRow}>
        <Text style={styles.verdictEmoji}>{vc.emoji}</Text>
        <Text style={styles.verdictHeadline}>{vc.headline}</Text>
      </View>

      {/* Health note chip */}
      {healthNote ? (
        <View style={styles.verdictNoteChip}>
          <Text style={styles.verdictNoteText} numberOfLines={3}>
            📝 Based on your note: {healthNote}
          </Text>
        </View>
      ) : null}

      {/* Summary */}
      <Text style={styles.verdictSummary}>{summary}</Text>

      {/* OK / Avoid columns */}
      {(ok_for.length > 0 || avoid_if.length > 0) && (
        <View style={styles.columnsRow}>
          <ConditionColumn
            title="✅  OK FOR"
            items={ok_for}
            healthNote={healthNote}
            isAvoid={false}
          />
          <ConditionColumn
            title="🚫  AVOID IF"
            items={avoid_if}
            healthNote={healthNote}
            isAvoid
          />
        </View>
      )}

      {/* Confidence */}
      <ConfidenceMeter value={confidence} color={colors.primary} />
    </View>
  );
}

// D) Fun facts
function FunFacts({ facts = [] }) {
  if (!facts.length) return null;
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>💡 Did You Know?</Text>
      {facts.map((fact, i) => (
        <View key={i} style={styles.factCard}>
          <Text style={styles.factText}>{fact}</Text>
        </View>
      ))}
    </View>
  );
}

// E) Specialists
function Specialists({ agentOutputs = [] }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>🧑‍⚕️ What our specialists said</Text>
      <Text style={styles.sectionSubtitle}>
        Each specialist reviewed your health note independently
      </Text>
      {agentOutputs.map((output, i) => {
        const agent = agents.find(a => a.id === output.agentId);
        if (!agent) return null;
        return (
          <AgentCard
            key={agent.id}
            agent={agent}
            output={output}
            delay={i * 150}
          />
        );
      })}
    </View>
  );
}

// ─── Main screen ─────────────────────────────────────────────────────────────
export default function ResultScreen({ navigation }) {
  const { image, healthNote, result } = useScan();

  const timestamp = useRef(
    new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  ).current;

  // Graceful fallback if result isn't ready
  if (!result) {
    return (
      <View style={styles.container}>
        <Background3D />
        <SafeAreaView style={styles.safeArea} edges={['top']}>
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No result yet.</Text>
          </View>
        </SafeAreaView>
      </View>
    );
  }

  const { product, type, servingSize, nutrition, conclusion, agentOutputs, funFacts } = result;

  return (
    <View style={styles.container}>
      <Background3D />

      <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>

        {/* ── Header ─────────────────────────────────────────────────── */}
        <View style={styles.header}>
          <Pressable
            onPress={() => navigation.goBack()}
            style={styles.backBtn}
            hitSlop={12}
          >
            <Text style={styles.backArrow}>‹</Text>
          </Pressable>
          <Text style={styles.headerTitle} numberOfLines={1}>{product}</Text>
          <View style={styles.headerSpacer} />
        </View>

        <ScrollView
          contentContainerStyle={styles.scroll}
          showsVerticalScrollIndicator={false}
        >
          {/* ── A: What you submitted ─────────────────────────────────── */}
          <Text style={styles.sectionTitle}>What You Submitted</Text>
          <SubmissionCard
            image={image}
            healthNote={healthNote}
            timestamp={timestamp}
            compact={false}
          />

          {/* ── B: Product card ───────────────────────────────────────── */}
          <ProductCard
            product={product}
            type={type}
            servingSize={servingSize}
            nutrition={nutrition}
          />

          {/* ── C: Verdict banner ─────────────────────────────────────── */}
          {conclusion && (
            <VerdictBanner conclusion={conclusion} healthNote={healthNote} />
          )}

          {/* ── D: Fun facts ──────────────────────────────────────────── */}
          <FunFacts facts={funFacts} />

          {/* ── E: Specialists ────────────────────────────────────────── */}
          <Specialists agentOutputs={agentOutputs} />

          <View style={{ height: 40 }} />
        </ScrollView>
      </SafeAreaView>
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

  // ── B: Glass product card ──
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
  // Two-column layout
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

  // ── D: Fun facts ──
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
