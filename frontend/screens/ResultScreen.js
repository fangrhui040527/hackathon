import React, { useRef, useState } from 'react';
import {
  Image,
  Modal,
  Pressable,
  ScrollView,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { colors } from '../constants/colors';
import { agents } from '../constants/agents';
import { useScan } from '../context/ScanContext';
import { useTheme } from '../context/ThemeContext';
import FoodBackground from '../components/FoodBackground';
import SubmissionCard from '../components/SubmissionCard';
import ConfidenceMeter from '../components/ConfidenceMeter';
import AgentCard from '../components/AgentCard';
import { styles, VERDICT_CONFIG } from './styles/ResultScreen.styles';

// ─── Nutrient icon map ────────────────────────────────────────────────────────
const NUTRIENT_ICONS = {
  'Calories': '🔥', 'Sugar': '🍬', 'Fat': '🧈', 'Sat. Fat': '🥩',
  'Sodium': '🧂', 'Carbs': '🌾', 'Protein': '💪', 'Fibre': '🌿',
};

// ─── Section heading with left-bar accent ────────────────────────────────────
function SectionHeading({ title, subtitle, accentColor }) {
  return (
    <View style={styles.sectionHeadRow}>
      <View style={[styles.sectionHeadBar, accentColor && { backgroundColor: accentColor }]} />
      <View style={{ flex: 1 }}>
        <Text style={styles.sectionTitle}>{title}</Text>
        {subtitle ? <Text style={styles.sectionSubtitle}>{subtitle}</Text> : null}
      </View>
    </View>
  );
}

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

// B) Product card
function ProductCard({ product, type, servingSize, nutrition = [] }) {
  return (
    <View style={styles.productCard}>
      {/* Badge + name row */}
      <View style={styles.productCardTop}>
        <View style={styles.productScanBadge}>
          <Text style={styles.productScanBadgeText}>✓ SCANNED</Text>
        </View>
      </View>

      <Text style={styles.productName}>{product}</Text>

      {/* Tags row */}
      {(type || servingSize) ? (
        <View style={styles.productTagsRow}>
          {type ? (
            <View style={styles.productTag}>
              <Text style={styles.productTagText}>{type}</Text>
            </View>
          ) : null}
          {servingSize ? (
            <View style={styles.productTag}>
              <Text style={styles.productTagText}>📏 {servingSize}</Text>
            </View>
          ) : null}
        </View>
      ) : null}

      {/* Nutrition grid */}
      {nutrition.length > 0 && (
        <>
          <View style={styles.nutriDivider} />
          <View style={styles.nutriGrid}>
            {nutrition.map((item, i) => (
              <View key={i} style={styles.nutriCell}>
                <Text style={styles.nutriIcon}>{NUTRIENT_ICONS[item.label] ?? '•'}</Text>
                <Text style={styles.nutriValue}>{item.value}</Text>
                <Text style={styles.nutriLabel}>{item.label}</Text>
              </View>
            ))}
          </View>
        </>
      )}
    </View>
  );
}

// C) Verdict banner — hero layout
function VerdictBanner({ conclusion, healthNote }) {
  const {
    verdict = 'caution',
    summary = '',
    ok_for = [],
    avoid_if = [],
    confidence = 0,
  } = conclusion;

  const vc = VERDICT_CONFIG[verdict] ?? VERDICT_CONFIG.caution;
  const pct = confidence > 1 ? Math.round(confidence) : Math.round(confidence * 100);

  return (
    <View style={[styles.verdictCard, { borderColor: vc.border, backgroundColor: vc.bg }]}>
      {/* Hero: emoji + label pill + headline */}
      <View style={styles.verdictHero}>
        <View style={[styles.verdictEmojiRing, { borderColor: vc.glowColor + '55', backgroundColor: vc.glowColor + '14' }]}>
          <Text style={styles.verdictHeroEmoji}>{vc.emoji}</Text>
        </View>
        <View style={[styles.verdictLabelPill, { backgroundColor: vc.glowColor + '1A', borderColor: vc.glowColor + '55' }]}>
          <Text style={[styles.verdictLabelText, { color: vc.glowColor }]}>{vc.label}</Text>
        </View>
        <Text style={styles.verdictHeadline}>{vc.headline}</Text>
      </View>

      {/* Gradient divider */}
      <LinearGradient
        colors={['transparent', vc.glowColor + '44', 'transparent']}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
        style={styles.verdictGradientDivider}
      />

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
          <View style={[styles.column, styles.columnOk]}>
            <Text style={styles.columnTitle}>✅  OK FOR</Text>
            {ok_for.map((item, i) => (
              <View key={i} style={styles.columnItemRow}>
                <View style={[styles.columnDot, { backgroundColor: '#00B341' }]} />
                <Text style={styles.columnItem}>{item}</Text>
              </View>
            ))}
          </View>
          <View style={[styles.column, styles.columnAvoid]}>
            <Text style={styles.columnTitle}>🚫  AVOID IF</Text>
            {avoid_if.map((item, i) => {
              const matched = matchesHealthNote(item, healthNote);
              return (
                <View key={i} style={styles.columnItemRow}>
                  <View style={[styles.columnDot, { backgroundColor: matched ? '#E53935' : '#E6A817' }]} />
                  <Text style={[styles.columnItem, matched && styles.columnItemMatch]}>
                    {item}{matched ? '  ← you' : ''}
                  </Text>
                </View>
              );
            })}
          </View>
        </View>
      )}

      {/* Confidence */}
      <View style={styles.confidenceWrapper}>
        <ConfidenceMeter value={pct} color={vc.glowColor} />
      </View>
    </View>
  );
}

// D) Fun facts — numbered cards
function FunFacts({ facts = [], isDark, palette }) {
  if (!facts.length) return null;
  return (
    <View style={styles.section}>
      <SectionHeading title="💡 Did You Know?" subtitle="Interesting facts about this product" accentColor="#d3d5d4" />
      {facts.map((fact, i) => (
        <View key={i} style={styles.factCard}>
          <View style={styles.factNumber}>
            <Text style={styles.factNumberText}>{String(i + 1).padStart(2, '0')}</Text>
          </View>
          <Text style={[styles.factText, !isDark && { color: palette.text1 }]}>{fact}</Text>
        </View>
      ))}
    </View>
  );
}

// E) Specialists — tap an avatar to reveal that specialist's analysis
function Specialists({ agentOutputs = [] }) {
  const [selectedId, setSelectedId] = useState(null);

  const selectedOutput = selectedId
    ? agentOutputs.find(o => o.agentId === selectedId)
    : null;
  const selectedAgent = selectedId
    ? agents.find(a => a.id === selectedId)
    : null;

  return (
    <View style={styles.section}>
      <SectionHeading
        title="🧑‍⚕️ Specialists"
        subtitle="Tap an icon to see their analysis"
        accentColor="#C3A6FF"
      />
      <View style={styles.teamRow}>
        {agents.map(a => {
          const active = selectedId === a.id;
          return (
            <Pressable
              key={a.id}
              onPress={() => setSelectedId(active ? null : a.id)}
              style={[
                styles.teamAvatar,
                {
                  backgroundColor: active ? a.color + '30' : a.color + '18',
                  borderColor: active ? a.color : a.color + '44',
                  transform: [{ scale: active ? 1.1 : 1 }],
                },
              ]}
              hitSlop={8}
            >
              <Text style={styles.teamAvatarEmoji}>{a.emoji}</Text>
            </Pressable>
          );
        })}
      </View>
      {selectedAgent && selectedOutput ? (
        <AgentCard agent={selectedAgent} output={selectedOutput} delay={0} />
      ) : null}
    </View>
  );
}

// ─── Main screen ─────────────────────────────────────────────────────────────
export default function ResultScreen({ navigation }) {
  const { image, healthNote, result } = useScan();
  const { isDark, palette } = useTheme();
  const [imageModalOpen, setImageModalOpen] = useState(false);

  const timestamp = useRef(
    new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  ).current;

  // Graceful fallback if result isn't ready
  if (!result) {
    return (
      <View style={[styles.container, !isDark && { backgroundColor: palette.deep }]}>
        <FoodBackground />
        <SafeAreaView style={styles.safeArea} edges={['top']}>
          <View style={styles.emptyState}>
            <Text style={[styles.emptyText, !isDark && { color: palette.text2 }]}>No result yet.</Text>
          </View>
        </SafeAreaView>
      </View>
    );
  }

  const { product, type, servingSize, nutrition, conclusion, agentOutputs, funFacts } = result;

  const handleChatWithAgent = (agent) => {
    setSelectedAgent(agent);
    navigation.navigate('Chat', { agentChat: true });
  };

  return (
    <View style={[styles.container, !isDark && { backgroundColor: palette.deep }]}>
      <FoodBackground />

      <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>

        {/* ── Header ─────────────────────────────────────────────────── */}
        <View style={[styles.header, !isDark && { backgroundColor: palette.surface, borderBottomColor: palette.border }]}>
          <Pressable
            onPress={() => navigation.goBack()}
            style={styles.backBtn}
            hitSlop={12}
          >
            <Text style={[styles.backArrow, !isDark && { color: palette.text1 }]}>‹</Text>
          </Pressable>
          <Text style={[styles.headerTitle, !isDark && { color: palette.text1 }]} numberOfLines={1}>{product}</Text>
          <View style={styles.headerSpacer} />
        </View>

        <ScrollView
          contentContainerStyle={styles.scroll}
          showsVerticalScrollIndicator={false}
        >
          {/* ── A: What you submitted ─────────────────────────────────── */}
          <SectionHeading title="What You Submitted" accentColor="#d3d5d4" />
          <SubmissionCard
            image={image}
            healthNote={healthNote}
            timestamp={timestamp}
            compact={false}            onImagePress={() => setImageModalOpen(true)}          />

          {/* ── B: Product card ───────────────────────────────────────── */}
          <SectionHeading title="Product Analysis" accentColor="#d3d5d4" />
          <ProductCard
            product={product}
            type={type}
            servingSize={servingSize}
            nutrition={nutrition}
          />

          {/* ── C: Verdict banner ─────────────────────────────────────── */}
          <SectionHeading title="Health Verdict" accentColor="#d3d5d4" />
          {conclusion && (
            <VerdictBanner conclusion={conclusion} healthNote={healthNote} />
          )}

          {/* ── D: Fun facts ──────────────────────────────────────────── */}
          <FunFacts facts={funFacts} isDark={isDark} palette={palette} />

          {/* ── E: Specialists ────────────────────────────────────────── */}
          <Specialists agentOutputs={agentOutputs} onChatWithAgent={handleChatWithAgent} />

          <View style={{ height: 40 }} />
        </ScrollView>
      </SafeAreaView>

      {/* ── Full-screen image modal ─────────────────────────────── */}
      <Modal
        visible={imageModalOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setImageModalOpen(false)}
      >
        <Pressable style={styles.imageModalOverlay} onPress={() => setImageModalOpen(false)}>
          {image ? (
            <Image
              source={{ uri: image }}
              style={styles.imageModalImg}
              resizeMode="contain"
            />
          ) : null}
          <View style={styles.imageModalClose}>
            <Text style={styles.imageModalCloseText}>✕</Text>
          </View>
        </Pressable>
      </Modal>
    </View>
  );
}
