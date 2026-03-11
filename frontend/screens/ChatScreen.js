// TODO: Replace mock pipeline with real SSE stream:
// POST /api/analyze (multipart: image + healthNote)
// event: { stage, label } — updates stageLabel in chat
// event: { stage: 'done', data: result } — swaps placeholder for result card

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Animated,
  Image,
  KeyboardAvoidingView,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker';
import { colors } from '../constants/colors';
import { useScan } from '../context/ScanContext';
import FoodBackground from '../components/FoodBackground';
import BurgerMenu from '../components/BurgerMenu';
import VerdictBadge from '../components/VerdictBadge';
import { useTheme } from '../context/ThemeContext';
import { API_URL } from '../constants/api';
import EventSource from 'react-native-sse';
import { styles, rs, V_BG, V_BORDER } from './styles/ChatScreen.styles';

// ─── Analysis pipeline stages ─────────────────────────────────────────────────
const PIPELINE_STAGES = [
  { icon: '📤', label: 'Uploading photo',            detail: 'Sending image to analysis pipeline...',           duration: 900  },
  { icon: '🔍', label: 'Reading label',              detail: 'Extracting text from nutrition label...',          duration: 1300 },
  { icon: '🩺', label: 'Dr. Chen',                   detail: 'Medical doctor reviewing metabolic risk...',       duration: 1200 },
  { icon: '🥗', label: 'Dr. Patel',                  detail: 'Nutritionist assessing calorie density...',        duration: 1100 },
  { icon: '⚗️',  label: 'Dr. Kim',                   detail: 'Chemist scanning for additives & preservatives...', duration: 1200 },
  { icon: '💪', label: 'Marcus',                     detail: 'Fitness expert evaluating glycaemic impact...',    duration: 1000 },
  { icon: '🏥', label: 'Dr. Amara',                  detail: 'Healthcare specialist checking long-term risks...', duration: 1100 },
  { icon: '🧠', label: 'Summarizing',                detail: 'Combining all specialist findings...',             duration: 1300 },
];

// ─── Suggestion chips ─────────────────────────────────────────────────────────
const SUGGESTIONS = [
  'Is this ok for kids?',
  'What should I eat instead?',
  'Explain the ingredients',
  'How much is too much?',
];

// ─── Mock text response ───────────────────────────────────────────────────────
function getMockResponse(message) {
  const lower = message.toLowerCase();
  if (/kid|child|children/.test(lower)) {
    return (
      'Based on the analysis, here are the guidelines for children:\n\n' +
      '• Check the sugar content — keep under 10 g per serving\n' +
      '• Once-a-week treat if high sugar, not daily\n' +
      '• Pair snacks with protein to slow sugar absorption\n' +
      '• Under 5 years old — stick to whole foods\n\n' +
      'Scan a product to get a personalized assessment 😊'
    );
  }
  if (/instead|alternative/.test(lower)) {
    return (
      'Better snack options with similar satisfaction:\n\n' +
      '• Dark chocolate (70%+) — less sugar, antioxidants\n' +
      '• Rice cakes with peanut butter — protein + crunch\n' +
      '• Fresh fruit with yogurt — natural sugars + fiber\n' +
      '• Nuts and dried fruit — energy without the crash 🥜'
    );
  }
  if (/ingredient/.test(lower)) {
    return (
      'I can analyze ingredients once you scan a product label.\n\n' +
      'Common things I look for:\n' +
      '• Synthetic additives & preservatives\n' +
      '• High-risk emulsifiers\n' +
      '• Hidden sugars under alternate names\n' +
      '• IARC-classified carcinogens\n\n' +
      'Take a photo of a nutrition label to get started 🔬'
    );
  }
  if (/how much|too much/.test(lower)) {
    return (
      'Safe consumption depends on the specific product.\n\n' +
      'General guidelines:\n' +
      '• Check sugar: keep under 25 g/day total (women) or 36 g/day (men)\n' +
      '• Watch sodium: under 2300 mg/day\n' +
      '• Limit ultra-processed (NOVA 4) foods to occasional treats\n\n' +
      'Scan a label and I\'ll give you specific guidance 📊'
    );
  }
  return (
    'I\'m here to help analyze your food products!\n\n' +
    'Scan a nutrition label or ask me about ingredients, nutrition, or healthier alternatives 😊'
  );
}

// ─── Typing / thinking dots ───────────────────────────────────────────────────
function BounceDots({ style }) {
  const anims = useRef([
    new Animated.Value(0),
    new Animated.Value(0),
    new Animated.Value(0),
  ]).current;

  useEffect(() => {
    const timers = anims.map((anim, i) => {
      const t = setTimeout(() => {
        Animated.loop(
          Animated.sequence([
            Animated.timing(anim, { toValue: -4, duration: 240, useNativeDriver: true }),
            Animated.timing(anim, { toValue: 0,  duration: 240, useNativeDriver: true }),
            Animated.delay(480),
          ]),
        ).start();
      }, i * 160);
      return t;
    });
    return () => {
      timers.forEach(t => clearTimeout(t));
      anims.forEach(a => a.stopAnimation());
    };
  }, []);

  return (
    <View style={[styles.dotsRow, style]}>
      {anims.map((anim, i) => (
        <Animated.View
          key={i}
          style={[styles.dot, { transform: [{ translateY: anim }] }]}
        />
      ))}
    </View>
  );
}

// ─── Claude-style thinking panel ─────────────────────────────────────────────
function AnalyzingMessage({ stageIndex }) {
  const [collapsed, setCollapsed] = useState(false);
  const active = PIPELINE_STAGES[Math.min(stageIndex, PIPELINE_STAGES.length - 1)];

  return (
    <View style={styles.msgRowAI}>
      <Image source={require('../../assets/HealthLensAI_Logo.png')} style={styles.aiAvatarImg} />

      <View style={styles.thinkingPanel}>
        {/* ── Header (always visible, tap to collapse) ── */}
        <Pressable
          style={styles.thinkingHeader}
          onPress={() => setCollapsed(v => !v)}
        >
          <BounceDots />
          <Text style={styles.thinkingTitle} numberOfLines={1}>
            {collapsed
              ? `${active.icon}  ${active.label}...`
              : 'Analyzing your scan...'}
          </Text>
          <Text style={styles.thinkingChevron}>{collapsed ? '›' : '▾'}</Text>
        </Pressable>

        {/* ── Stage list (expandable) ── */}
        {!collapsed && (
          <View style={styles.stageList}>
            {PIPELINE_STAGES.map((stage, i) => {
              const isDone    = i < stageIndex;
              const isActive  = i === stageIndex;

              return (
                <View
                  key={i}
                  style={[styles.stageRow, i > 0 && styles.stageRowBorder]}
                >
                  {/* Status circle */}
                  <View style={[
                    styles.stageCircle,
                    isDone   && styles.stageCircleDone,
                    isActive && styles.stageCircleActive,
                  ]}>
                    <Text style={[
                      styles.stageCircleText,
                      isDone   && styles.stageCircleTextDone,
                      isActive && styles.stageCircleTextActive,
                    ]}>
                      {isDone ? '✓' : stage.icon}
                    </Text>
                  </View>

                  {/* Label + detail */}
                  <View style={{ flex: 1 }}>
                    <Text style={[
                      styles.stageLabel,
                      isDone   && styles.stageLabelDone,
                      isActive && styles.stageLabelActive,
                    ]}>
                      {stage.label}
                    </Text>
                    {isActive && (
                      <Text style={styles.stageDetail}>{stage.detail}</Text>
                    )}
                  </View>

                  {/* Active: bouncing dots */}
                  {isActive && <BounceDots />}
                </View>
              );
            })}
          </View>
        )}
      </View>
    </View>
  );
}

// ─── Compact result card (stays in chat history) ──────────────────────────────
function ResultMessage({ result, onViewFullAnalysis }) {
  const verdict = result.conclusion?.verdict ?? 'caution';

  return (
    <View style={styles.msgRowAI}>
      <Image source={require('../../assets/HealthLensAI_Logo.png')} style={styles.aiAvatarImg} />

      <View style={[
        styles.resultCard,
        { backgroundColor: V_BG[verdict], borderColor: V_BORDER[verdict] },
      ]}>

        {/* Product + verdict badge */}
        <View style={rs.header}>
          <View style={{ flex: 1, marginRight: 10 }}>
            <Text style={rs.product}>{result.product}</Text>
            <Text style={rs.type}>{result.type} · {result.servingSize}</Text>
          </View>
          <VerdictBadge verdict={verdict} />
        </View>

        {/* Confidence bar */}
        <View style={rs.confRow}>
          <Text style={rs.confLabel}>Confidence</Text>
          <View style={rs.confBarBg}>
            <View style={[rs.confBarFill, { width: `${result.conclusion.confidence}%` }]} />
          </View>
          <Text style={rs.confPct}>{result.conclusion.confidence}%</Text>
        </View>

        {/* Summary */}
        <Text style={rs.summary}>{result.conclusion.summary}</Text>

        {/* View full analysis button */}
        <Pressable onPress={onViewFullAnalysis} style={rs.fullAnalysisBtn}>
          <Text style={rs.fullAnalysisBtnText}>View Full Analysis  ›</Text>
        </Pressable>
      </View>
    </View>
  );
}

// ─── Main screen ──────────────────────────────────────────────────────────────
export default function ChatScreen({ navigation, route }) {
  const insets = useSafeAreaInsets();
  const { image, healthNote, result, setResult } = useScan();

  const [messages, setMessages]                   = useState([]);
  const [inputText, setInputText]                 = useState('');
  const [isTyping, setIsTyping]                   = useState(false);
  const [pendingAttachment, setPendingAttachment] = useState(null); // { uri }
  const [menuOpen, setMenuOpen]                   = useState(false);

  const scrollRef        = useRef(null);
  const typingTimerRef   = useRef(null);
  const analysisTimerRef = useRef(null);
  const menuAnim         = useRef(new Animated.Value(0)).current;

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    const t = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 80);
    return () => clearTimeout(t);
  }, [messages, isTyping]);

  // Cleanup timers on unmount
  useEffect(() => () => {
    if (typingTimerRef.current)   clearTimeout(typingTimerRef.current);
    if (analysisTimerRef.current) clearTimeout(analysisTimerRef.current);
  }, []);

  // Trigger analysis when navigated here from Preview (or Scan)
  useFocusEffect(
    useCallback(() => {
      if (route.params?.triggerAnalysis && image) {
        navigation.setParams({ triggerAnalysis: false });
        startAnalysis(image, healthNote);
      }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [route.params?.triggerAnalysis]),
  );

  // ── Stage name → pipeline index mapping ──────────────────────────────────────
  const STAGE_MAP = {
    upload: 0, extract: 1, grounding: 1,
    agent1: 2, agent2: 3, agent3: 4, agent4: 5, agent5: 6,
    conclude: 7, done: 8,
  };

  // ── Analysis pipeline (real SSE to backend) ─────────────────────────────────
  const startAnalysis = (imageUri, caption) => {
    if (analysisTimerRef.current) clearTimeout(analysisTimerRef.current);

    const userMsgId   = `user_img_${Date.now()}`;
    const analyzingId = `analyzing_${Date.now()}`;

    // Add user image + analyzing placeholder in one update
    setMessages(prev => [
      ...prev,
      { id: userMsgId,   type: 'user_image',  imageUri, caption: caption || null },
      { id: analyzingId, type: 'ai_analyzing', stageIndex: 0 },
    ]);

    // Build multipart form data
    const formData = new FormData();
    formData.append('image', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'photo.jpg',
    });
    formData.append('healthNote', caption || '');

    // Send to backend and stream SSE events via react-native-sse
    const es = new EventSource(`${API_URL}/api/analyze`, {
      method: 'POST',
      body: formData,
      headers: {
        Accept: 'text/event-stream',
        'ngrok-skip-browser-warning': 'true',
      },
      pollingInterval: 0,
    });

    // Timeout: if no event arrives within 15s, backend is likely unreachable
    let connectTimeout = setTimeout(() => {
      es.close();
      fallbackToError(analyzingId);
    }, 15000);

    es.addEventListener('stage', (event) => {
      if (connectTimeout) { clearTimeout(connectTimeout); connectTimeout = null; }
      try {
        const payload = JSON.parse(event.data);
        handleSSEEvent(analyzingId, 'stage', payload);
        if (payload.stage === 'done') es.close();
      } catch (e) {
        // ignore parse errors
      }
    });

    es.addEventListener('error', (event) => {
      if (connectTimeout) { clearTimeout(connectTimeout); connectTimeout = null; }
      if (event.data) {
        try {
          const payload = JSON.parse(event.data);
          console.error('Backend error:', payload.error);
        } catch (_) {}
      }
      es.close();
      fallbackToError(analyzingId);
    });

    es.addEventListener('close', () => es.close());
  };

  // Handle incoming SSE events
  const handleSSEEvent = (analyzingId, eventType, payload) => {
    if (eventType === 'error') {
      console.error('Backend error:', payload.error);
      fallbackToError(analyzingId);
      return;
    }

    const stageIndex = STAGE_MAP[payload.stage] ?? 0;

    if (payload.stage === 'done' && payload.data) {
      // Pipeline complete — replace analyzing with result
      setResult(payload.data);
      setMessages(prev =>
        prev.map(m =>
          m.id === analyzingId
            ? { id: analyzingId, type: 'ai_result', result: payload.data }
            : m,
        ),
      );
    } else {
      // Update stage progress
      setMessages(prev =>
        prev.map(m =>
          m.id === analyzingId ? { ...m, stageIndex } : m,
        ),
      );
    }
  };

  // Show error message if backend is unreachable
  const fallbackToError = (analyzingId) => {
    setMessages(prev =>
      prev.map(m =>
        m.id === analyzingId
          ? { id: analyzingId, type: 'ai_text', text: 'Sorry, the analysis server is currently unreachable. Please make sure the backend is running and try again.' }
          : m,
      ),
    );
  };

  // ── Send text message ───────────────────────────────────────────────────────
  const handleSend = (textOverride) => {
    // Pending image attachment takes priority
    if (textOverride === undefined && pendingAttachment) {
      handleSendWithAttachment();
      return;
    }

    const trimmed = (typeof textOverride === 'string' ? textOverride : inputText).trim();
    if (!trimmed) return;

    if (typeof textOverride !== 'string') setInputText('');

    setMessages(prev => [
      ...prev,
      { id: String(Date.now()), type: 'user_text', text: trimmed },
    ]);
    setIsTyping(true);

    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    typingTimerRef.current = setTimeout(() => {
      setIsTyping(false);
      setMessages(prev => [
        ...prev,
        { id: String(Date.now() + 1), type: 'ai_text', text: getMockResponse(trimmed) },
      ]);
    }, 1400);
  };

  // ── Gallery pick from input bar ─────────────────────────────────────────────
  const handleGalleryPick = async () => {
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!res.canceled && res.assets?.[0]?.uri) {
      setPendingAttachment({ uri: res.assets[0].uri });
    }
  };

  // ── Send pending image attachment ───────────────────────────────────────────
  const handleSendWithAttachment = () => {
    const att     = pendingAttachment;
    const caption = inputText.trim() || null;
    setPendingAttachment(null);
    setInputText('');
    startAnalysis(att.uri, caption);
  };

  const openMenu = () => {
    setMenuOpen(true);
    Animated.spring(menuAnim, { toValue: 1, useNativeDriver: true, tension: 140, friction: 11 }).start();
  };
  const closeMenu = () => {
    Animated.timing(menuAnim, { toValue: 0, duration: 160, useNativeDriver: true }).start(() => setMenuOpen(false));
  };
  const toggleMenu = () => (menuOpen ? closeMenu() : openMenu());

  const handleClearChat = () => {
    closeMenu();
    setMessages([]);
  };

  const chatIsEmpty = messages.length === 0 && !isTyping;
  const canSend     = !!pendingAttachment || !!inputText.trim();

  const { isDark, palette } = useTheme();
  const [burgerOpen, setBurgerOpen] = useState(false);

  return (
    <View style={[styles.container, !isDark && { backgroundColor: palette.deep }]}>
      <FoodBackground />
      <BurgerMenu
        visible={burgerOpen}
        onClose={() => setBurgerOpen(false)}
        navigation={navigation}
        onClearChat={handleClearChat}
      />

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior="padding"
        keyboardVerticalOffset={0}
      >
        {/* ── Header ───────────────────────────────────────────────────── */}
        <View style={[styles.header, { paddingTop: insets.top + 8 }, !isDark && { backgroundColor: palette.surface }]}>
          <View style={{ width: 38 }} />

          <View style={styles.headerCenter}>
            <Text style={[styles.headerTitle, !isDark && { color: palette.text1 }]}>HealthScan AI</Text>
            <Text style={[styles.headerSub, !isDark && { color: palette.text2 }]} numberOfLines={1}>
              {result ? result.product : 'Powered by 5 AI specialists'}
            </Text>
          </View>

          {/* Burger menu button */}
          <Pressable
            onPress={() => setBurgerOpen(true)}
            style={[styles.headerBackBtn, !isDark && { backgroundColor: palette.surface2 }]}
            hitSlop={8}
          >
            <View style={styles.burgerWrap}>
              <View style={[styles.burgerBar, !isDark && { backgroundColor: '#E8ECF4' }]} />
              <View style={[styles.burgerBar, { width: 13 }, !isDark && { backgroundColor: '#E8ECF4' }]} />
              <View style={[styles.burgerBar, !isDark && { backgroundColor: '#E8ECF4' }]} />
            </View>
          </Pressable>
        </View>

        {/* ── Messages ─────────────────────────────────────────────────── */}
        <ScrollView
          ref={scrollRef}
          style={[styles.messagesScroll, { flexShrink: 1 }]}
          contentContainerStyle={[
            styles.messagesContent,
            chatIsEmpty && styles.messagesContentEmpty,
          ]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          onScrollBeginDrag={closeMenu}
        >
          {/* Empty state */}
          {chatIsEmpty && (
            <View style={styles.emptyState}>
              <Image
                source={require('../../assets/HealthLensAI_Logo.png')}
                style={styles.emptyLogo}
              />
              <Text style={[styles.emptyTitle, !isDark && { color: palette.text1 }]}>Your AI Food Analyst</Text>
              <Text style={[styles.emptyHint, !isDark && { color: palette.text2 }]}>
                Scan any nutrition label for an instant expert breakdown
              </Text>
              <View style={styles.emptyFeatures}>
                {[
                  { icon: '🔬', label: 'Ingredient Scanner' },
                  { icon: '🩺', label: '5 AI Specialists' },
                  { icon: '📊', label: 'Nutrition Insights' },
                ].map((f, i) => (
                  <View key={i} style={[styles.featurePill, !isDark && { backgroundColor: palette.surface2 }]}>
                    <Text style={styles.featurePillIcon}>{f.icon}</Text>
                    <Text style={[styles.featurePillText, !isDark && { color: '#E8ECF4' }]}>{f.label}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Message list */}
          {messages.map(msg => {
            if (msg.type === 'user_text') {
              return (
                <View key={msg.id} style={styles.msgRowUser}>
                  <View style={[styles.msgBubbleUser, !isDark && { backgroundColor: palette.accent }]}>
                    <Text style={[styles.msgTextUser, !isDark && { color: '#0d131a' }]}>{msg.text}</Text>
                  </View>
                </View>
              );
            }

            if (msg.type === 'user_image') {
              return (
                <View key={msg.id} style={styles.msgRowUser}>
                  <View style={[styles.msgBubbleUser, styles.msgBubbleImage, !isDark && { backgroundColor: palette.accent }]}>
                    <Image
                      source={{ uri: msg.imageUri }}
                      style={styles.msgImage}
                      resizeMode="cover"
                    />
                    {msg.caption ? (
                      <Text style={[styles.msgTextUser, { marginTop: 8, paddingHorizontal: 14 }]}>
                        {msg.caption}
                      </Text>
                    ) : null}
                  </View>
                </View>
              );
            }

            if (msg.type === 'ai_text') {
              return (
                <View key={msg.id} style={styles.msgRowAI}>
                  <Image source={require('../../assets/HealthLensAI_Logo.png')} style={styles.aiAvatarImg} />
                  <View style={styles.msgBubbleAI}>
                    <Text style={styles.msgTextAI}>{msg.text}</Text>
                  </View>
                </View>
              );
            }

            if (msg.type === 'ai_analyzing') {
              return <AnalyzingMessage key={msg.id} stageIndex={msg.stageIndex} />;
            }

            if (msg.type === 'ai_result') {
              return (
                <ResultMessage
                  key={msg.id}
                  result={msg.result}
                  onViewFullAnalysis={() => navigation.navigate('Result')}
                />
              );
            }

            return null;
          })}

          {isTyping && (
            <View style={styles.msgRowAI}>
              <Image source={require('../../assets/HealthLensAI_Logo.png')} style={styles.aiAvatarImg} />
              <View style={[styles.msgBubbleAI, { paddingVertical: 16 }]}>
                <BounceDots />
              </View>
            </View>
          )}
        </ScrollView>

        {/* ── Bottom area ───────────────────────────────────────────────── */}
        <View style={styles.bottomArea}>

          {/* ── Pop-up menu ────────────────────────────────────────────── */}
          <Animated.View
            pointerEvents={menuOpen ? 'box-none' : 'none'}
            style={[
              styles.popMenu,
              !isDark && { backgroundColor: '#F5F5F5', borderColor: 'rgba(0,0,0,0.10)' },
              {
                opacity: menuAnim,
                transform: [
                  {
                    translateY: menuAnim.interpolate({
                      inputRange:  [0, 1],
                      outputRange: [14, 0],
                    }),
                  },
                  {
                    scale: menuAnim.interpolate({
                      inputRange:  [0, 1],
                      outputRange: [0.93, 1],
                    }),
                  },
                ],
              },
            ]}
          >
            <Pressable
              style={styles.popMenuItem}
              onPress={() => { closeMenu(); navigation.navigate('Scan'); }}
            >
              <Image source={require('../../assets/BCamera_Icon.png')} style={[styles.popMenuItemImg, { tintColor: isDark ? '#FFFFFF' : '#0d131a' }, !isDark && { width: 40, height: 40 }]} />
              <Text style={[styles.popMenuItemLabel, !isDark && { color: '#0d131a' }]}>Take a Photo</Text>
            </Pressable>

            <View style={styles.popMenuDivider} />

            <Pressable
              style={styles.popMenuItem}
              onPress={() => { closeMenu(); handleGalleryPick(); }}
            >
              <Image source={require('../../assets/BImage_Icon.png')} style={[styles.popMenuItemImg, { tintColor: isDark ? '#FFFFFF' : '#0d131a' }, !isDark && { width: 40, height: 40 }]} />
              <Text style={[styles.popMenuItemLabel, !isDark && { color: '#0d131a' }]}>Upload from Gallery</Text>
            </Pressable>

            {result && (
              <>
                <View style={styles.popMenuDivider} />
                <Pressable
                  style={styles.popMenuItem}
                  onPress={() => { closeMenu(); navigation.navigate('Result'); }}
                >
                  <Text style={styles.popMenuItemIcon}>🔍</Text>
                  <Text style={[styles.popMenuItemLabel, !isDark && { color: '#0d131a' }]}>View Last Analysis</Text>
                </Pressable>
              </>
            )}

            <View style={styles.popMenuDivider} />

            <Pressable style={styles.popMenuItem} onPress={handleClearChat}>
              <Image source={require('../../assets/Btrash_Icon.png')} style={[styles.popMenuItemImg, { tintColor: isDark ? '#FFFFFF' : '#0d131a' }, !isDark && { width: 40, height: 40 }]} />
              <Text style={styles.popMenuItemLabelDanger}>Clear Chat</Text>
            </Pressable>
          </Animated.View>

          {/* ── Suggestion chips (empty state only) ────────────────────── */}
          {chatIsEmpty && (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.chipsRow}
              style={styles.chipsScroll}
              keyboardShouldPersistTaps="handled"
            >
              {SUGGESTIONS.map((s, i) => (
                <Pressable key={i} onPress={() => handleSend(s)} style={[styles.chip, !isDark && { backgroundColor: '#EFEFEF', borderColor: 'rgba(0,0,0,0.10)' }]}>
                  <Text style={[styles.chipText, !isDark && { color: '#0d131a' }]}>{s}</Text>
                </Pressable>
              ))}
            </ScrollView>
          )}

          {/* ── Pending image preview strip ─────────────────────────────── */}
          {pendingAttachment && (
            <View style={[styles.attachmentStrip, !isDark && { backgroundColor: palette.surface }]}>
              <Image source={{ uri: pendingAttachment.uri }} style={styles.attachmentThumb} />
              <Pressable
                onPress={() => setPendingAttachment(null)}
                style={styles.attachmentRemove}
                hitSlop={8}
              >
                <Text style={styles.attachmentRemoveText}>✕</Text>
              </Pressable>
              <Text style={styles.attachmentHint}>Add a caption or send now</Text>
            </View>
          )}

          {/* ── Input bar ──────────────────────────────────────────────── */}
          <View style={[styles.inputBar, { paddingBottom: Math.max(insets.bottom, 14) }, !isDark && { backgroundColor: palette.surface }]}>
            {/* + button — opens attachment menu */}
            <Pressable onPress={toggleMenu} style={[styles.plusBtn, !isDark && { backgroundColor: '#EFEFEF', borderColor: 'rgba(0,0,0,0.10)' }]} hitSlop={8}>
              <Animated.Image
                source={require('../../assets/BMore_Icon.png')}
                style={[
                  styles.plusBtnIcon,
                  { tintColor: isDark ? '#FFFFFF' : '#0d131a' },
                  {
                    transform: [{
                      rotate: menuAnim.interpolate({
                        inputRange:  [0, 1],
                        outputRange: ['0deg', '45deg'],
                      }),
                    }],
                  },
                ]}
              />
            </Pressable>

            {/* Message input */}
            <TextInput
              style={[styles.textInput, !isDark && { backgroundColor: '#F5F5F5', color: '#0d131a', borderColor: 'rgba(0,0,0,0.12)' }]}
              value={inputText}
              onChangeText={setInputText}
              placeholder={pendingAttachment ? 'Add a caption...' : 'Message HealthScan AI...'}
              placeholderTextColor={!isDark ? '#9A9A9A' : colors.textSecondary}
              returnKeyType="send"
              onSubmitEditing={() => handleSend()}
              onFocus={closeMenu}
              blurOnSubmit={false}
              multiline
            />

            {/* Upload / send button */}
            <Pressable onPress={() => handleSend()} disabled={!canSend} hitSlop={4}>
              <LinearGradient
                colors={isDark ? ['#d3d5d4', '#b8babc'] : [palette.accent, '#D0D0D0']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={[styles.sendBtn, !canSend && styles.sendBtnDisabled]}
              >
                <Image source={require('../../assets/BSubmit_Icon.png')} style={[styles.sendIcon, { tintColor: isDark ? '#FFFFFF' : '#0d131a' }]} />
              </LinearGradient>
            </Pressable>
          </View>

        </View>
      </KeyboardAvoidingView>
    </View>
  );
}


