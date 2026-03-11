// TODO: Replace setTimeout simulation with real SSE:
// const source = new EventSource(`${API_URL}/api/analyze`, { method: 'POST', body: formData });
// source.onmessage = (e) => {
//   const { stage, message, data } = JSON.parse(e.data);
//   updateStage(stage);
//   if (stage === 'done') { setResult(data); navigate('Result'); }
// };

import React, { useEffect, useRef, useState } from 'react';
import { Animated, ScrollView, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '../constants/colors';
import { agents } from '../constants/agents';
import { useScan } from '../context/ScanContext';
import Background3D from '../components/Background3D';
import SubmissionCard from '../components/SubmissionCard';
import { styles } from './styles/LoadingScreen.styles';

// ─── Pipeline stages ─────────────────────────────────────────────────────────
const STAGES = [
  { id: 'upload',   icon: '📤', label: 'Uploading your photo...',       duration: 1200 },
  { id: 'extract',  icon: '🔍', label: 'Reading the label...',          duration: 1500 },
  { id: 'agent1',   icon: '🩺', label: 'Dr. Chen is reviewing...',      duration: 1400 },
  { id: 'agent2',   icon: '🥗', label: 'Dr. Patel is analyzing...',     duration: 1300 },
  { id: 'agent3',   icon: '⚗️',  label: 'Dr. Kim checking chemicals...', duration: 1400 },
  { id: 'agent4',   icon: '💪', label: 'Marcus assessing fitness...',   duration: 1200 },
  { id: 'agent5',   icon: '🏥', label: 'Dr. Amara reviewing risks...',  duration: 1300 },
  { id: 'conclude', icon: '🧠', label: 'Summarizing findings...',        duration: 1600 },
  { id: 'done',     icon: '✅', label: 'Done!',                          duration: 0    },
];

// ─── Mock result (Oreo cookies) ───────────────────────────────────────────────
const MOCK_RESULT = {
  product: 'Oreo Cookies',
  type: 'Ultra-Processed Snack',
  servingSize: '3 cookies (34 g)',
  nutrition: [
    { label: 'Calories', value: '160 kcal' },
    { label: 'Sugar',    value: '21 g'     },
    { label: 'Fat',      value: '7 g'      },
    { label: 'Sat. Fat', value: '3.5 g'    },
    { label: 'Sodium',   value: '135 mg'   },
    { label: 'Carbs',    value: '25 g'     },
    { label: 'Protein',  value: '< 1 g'    },
    { label: 'Fibre',    value: '0.5 g'    },
  ],
  funFacts: [
    'Oreos have been sold since 1912 — over 110 years old, yet they still contain no real vanilla extract.',
    'The cream filling is made entirely from vegetable shortening and sugar. There is no cream or dairy in it.',
    'Oreo is the world\'s best-selling cookie with over 40 billion produced annually across 100+ countries.',
    'Studies show the sugar–fat–salt ratio in Oreos activates the same dopamine reward pathways as habit-forming substances.',
    'Nabisco holds 40+ patents covering the Oreo\'s design, manufacturing process, and proprietary embossing pattern.',
  ],
  conclusion: {
    verdict: 'avoid',
    summary:
      'Oreo cookies are ultra-processed, high in refined sugar and saturated fat, ' +
      'with synthetic additives offering no meaningful nutritional value. Regular ' +
      'consumption poses measurable risk across metabolic, cardiovascular, and ' +
      'digestive health — particularly concerning for individuals with existing ' +
      'conditions. Occasional indulgence is low risk for healthy adults, but these ' +
      'should not be a dietary staple.',
    ok_for: [
      'Occasional rare treat',
      'Healthy adults with no metabolic issues',
      'Post-workout glycogen top-up (small amount)',
    ],
    avoid_if: [
      'Diabetes or insulin resistance',
      'High blood pressure',
      'Heart disease or high cholesterol',
      'Weight loss or calorie-deficit goals',
      'Gut health concerns or IBS',
    ],
    flags: ['Ultra-processed', 'High sugar', 'Synthetic additives', 'Low nutritional value'],
    confidence: 89,
  },
  agentOutputs: [
    {
      agentId: 1,
      verdict: 'avoid',
      summary:
        'Each serving (3 cookies, 34 g) contains 21 g of sugar — 42 % of the ' +
        'recommended daily limit. Chronic intake at this level elevates insulin ' +
        'resistance, triglyceride levels, and systolic blood pressure. Patients ' +
        'with diabetes, metabolic syndrome, or hypertension should treat this as a ' +
        'red-flag food and limit consumption strictly.',
      flags: ['21 g sugar/serving', 'High glycaemic index', 'Saturated fat 3.5 g', 'Raises triglycerides'],
      confidence: 91,
      considered_health_note: true,
    },
    {
      agentId: 2,
      verdict: 'caution',
      summary:
        'Oreos deliver 160 kcal per 3-cookie serving almost entirely from refined ' +
        'carbohydrates and fat, with negligible protein (< 1 g) and minimal fibre ' +
        '(0.5 g). The calorie-to-nutrient density ratio is extremely poor. They ' +
        'will not support satiety or micronutrient needs. Suitable only as a very ' +
        'occasional treat within a well-balanced diet.',
      flags: ['Empty calories', '< 1 g protein', '0.5 g fibre', '135 mg sodium'],
      confidence: 88,
      considered_health_note: false,
    },
    {
      agentId: 3,
      verdict: 'avoid',
      summary:
        'Ingredient analysis reveals vanillin (synthetic flavour), soy lecithin ' +
        '(emulsifier), and TBHQ traces (preservative). High-temperature baking of ' +
        'starchy dough generates measurable acrylamide — a probable human ' +
        'carcinogen per IARC. The palm oil fraction contains elevated levels of ' +
        'glycidyl esters, raising additional safety concerns with frequent use.',
      flags: ['Synthetic vanillin', 'TBHQ preservative', 'Acrylamide risk', 'Glycidyl esters'],
      confidence: 84,
      considered_health_note: false,
    },
    {
      agentId: 4,
      verdict: 'caution',
      summary:
        'Simple carbohydrates in Oreos cause a rapid glucose spike (GI ≈ 71) ' +
        'followed by a sharp crash — counterproductive for sustained athletic ' +
        'output or body composition goals. A small amount immediately post-workout ' +
        'could aid glycogen replenishment, but superior options exist. Avoid ' +
        'pre-workout entirely as they will impair endurance and focus.',
      flags: ['GI ≈ 71', 'No protein for recovery', 'Post-workout only at best', 'Poor body-comp food'],
      confidence: 77,
      considered_health_note: false,
    },
    {
      agentId: 5,
      verdict: 'avoid',
      summary:
        'Epidemiological data consistently links ultra-processed food consumption ' +
        '(NOVA group 4, which Oreos fall into) with a 12 % higher all-cause ' +
        'mortality risk, gut microbiome dysbiosis, and accelerated cellular ageing ' +
        'markers. The reward-pathway engagement of the sugar–fat–salt combination ' +
        'also elevates compulsive eating risk. From a preventive-health standpoint, ' +
        'these should be a genuine rarity in the diet.',
      flags: ['NOVA group 4', 'Microbiome disruption', 'Compulsive-eating risk', 'Longevity concern'],
      confidence: 86,
      considered_health_note: true,
    },
  ],
};

// ─── Bouncing-dots indicator (shown beside active step) ───────────────────────
function BounceDots() {
  const anims = useRef([
    new Animated.Value(0),
    new Animated.Value(0),
    new Animated.Value(0),
  ]).current;

  useEffect(() => {
    // Each dot runs an independent loop, staggered via setTimeout so delays
    // don't accumulate inside the Animated.loop sequence.
    const timers = anims.map((anim, i) => {
      const timer = setTimeout(() => {
        Animated.loop(
          Animated.sequence([
            Animated.timing(anim, { toValue: -5, duration: 260, useNativeDriver: true }),
            Animated.timing(anim, { toValue: 0,  duration: 260, useNativeDriver: true }),
            Animated.delay(480),
          ]),
        ).start();
      }, i * 160);
      return timer;
    });

    return () => {
      timers.forEach(t => clearTimeout(t));
      anims.forEach(a => a.stopAnimation());
    };
  }, []);

  return (
    <View style={styles.bounceDots}>
      {anims.map((anim, i) => (
        <Animated.View
          key={i}
          style={[styles.bounceDot, { transform: [{ translateY: anim }] }]}
        />
      ))}
    </View>
  );
}

// ─── Single step row ─────────────────────────────────────────────────────────
function StepRow({ stage, status }) {
  const isDone    = status === 'done';
  const isActive  = status === 'active';

  const circleColor = isDone
    ? colors.success
    : isActive
    ? colors.primary
    : 'rgba(255,255,255,0.10)';

  const labelColor = isDone
    ? colors.success
    : isActive
    ? colors.primary
    : colors.textSecondary;

  return (
    <View style={styles.stepRow}>
      {/* Circle indicator */}
      <View
        style={[
          styles.stepCircle,
          { backgroundColor: circleColor },
          isActive && styles.stepCircleGlow,
        ]}
      >
        <Text style={styles.stepCircleIcon}>{isDone ? '✓' : stage.icon}</Text>
      </View>

      {/* Label */}
      <Text style={[styles.stepLabel, { color: labelColor }]} numberOfLines={1}>
        {stage.label}
      </Text>

      {/* Bouncing dots — only on the active step */}
      {isActive && <BounceDots />}
    </View>
  );
}

// ─── Main screen ─────────────────────────────────────────────────────────────
export default function LoadingScreen({ navigation }) {
  const { image, healthNote, setResult } = useScan();

  const [activeIndex, setActiveIndex] = useState(0);

  // Stable timestamp generated once on mount
  const timestamp = useRef(
    new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  ).current;

  // Pulsing scale animation for the center icon
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.09, duration: 700, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1,    duration: 700, useNativeDriver: true }),
      ]),
    ).start();
  }, []);

  // Sequential pipeline simulation
  useEffect(() => {
    let idx = 0;
    let timeoutId;

    const advance = () => {
      setActiveIndex(idx);
      const stage = STAGES[idx];

      if (stage.id === 'done') {
        setResult(MOCK_RESULT);
        timeoutId = setTimeout(() => navigation.navigate('Result'), 500);
        return;
      }

      timeoutId = setTimeout(() => {
        idx += 1;
        advance();
      }, stage.duration);
    };

    advance();
    return () => clearTimeout(timeoutId);
  }, []);

  const currentStage = STAGES[activeIndex] ?? STAGES[STAGES.length - 1];

  return (
    <View style={styles.container}>
      <Background3D />

      <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
        <ScrollView
          contentContainerStyle={styles.scroll}
          showsVerticalScrollIndicator={false}
        >
          {/* ── Submission summary ─────────────────────────────────────── */}
          <SubmissionCard
            image={image}
            healthNote={healthNote}
            timestamp={timestamp}
            compact
          />

          {/* ── Green confirmation banner ──────────────────────────────── */}
          {healthNote ? (
            <View style={styles.banner}>
              <Text style={styles.bannerText}>
                ✅  Received — all specialists have your health note
              </Text>
            </View>
          ) : null}

          {/* ── Pulsing stage icon ─────────────────────────────────────── */}
          <View style={styles.centerSection}>
            <Animated.View
              style={[styles.iconBox, { transform: [{ scale: pulseAnim }] }]}
            >
              <Text style={styles.iconEmoji}>{currentStage.icon}</Text>
            </Animated.View>

            <Text style={styles.stageLabel}>{currentStage.label}</Text>
            <Text style={styles.stageSubtitle}>Usually takes 15–20 seconds</Text>
          </View>

          {/* ── Step list ─────────────────────────────────────────────── */}
          <View style={styles.stepList}>
            {STAGES.map((stage, i) => (
              <StepRow
                key={stage.id}
                stage={stage}
                status={
                  i < activeIndex ? 'done' :
                  i === activeIndex ? 'active' :
                  'pending'
                }
              />
            ))}
          </View>
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}
