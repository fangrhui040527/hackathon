import React, { useEffect, useRef } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';
import Markdown from 'react-native-markdown-display';
import { colors } from '../constants/colors';
import VerdictBadge from './VerdictBadge';
import ConfidenceMeter from './ConfidenceMeter';

export default function AgentCard({ agent, output, delay = 0, onChat }) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        delay,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 400,
        delay,
        useNativeDriver: true,
      }),
    ]).start();
  }, [delay]);

  if (!agent || !output) return null;

  const { name, role, emoji, color } = agent;
  const { verdict, considered_health_note, summary, flags = [], confidence = 0 } = output;

  return (
    <Animated.View
      style={[
        styles.card,
        {
          backgroundColor: color + '15',
          borderColor: color + '33',
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      {/* Header row: avatar + name/role + verdict badge */}
      <View style={styles.header}>
        <View style={[styles.avatar, { backgroundColor: color + '33' }]}>
          <Text style={styles.avatarEmoji}>{emoji}</Text>
        </View>

        <View style={styles.agentMeta}>
          <Text style={[styles.agentName, { color }]}>{name}</Text>
          <Text style={styles.agentRole}>{role}</Text>
        </View>

        <VerdictBadge verdict={verdict} small />
      </View>

      {/* Health note badge */}
      {considered_health_note && (
        <View style={styles.noteChip}>
          <Text style={styles.noteChipText}>📝 Considered your health note</Text>
        </View>
      )}

      {/* Summary */}
      {summary ? (
        <Markdown style={mdStyles}>{summary}</Markdown>
      ) : null}

      {/* Flag chips */}
      {flags.length > 0 && (
        <View style={styles.flagsRow}>
          {flags.map((flag, i) => (
            <View key={i} style={[styles.flagChip, { borderColor: color + '66' }]}>
              <Text style={styles.flagText}>{flag}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Confidence meter */}
      <ConfidenceMeter value={confidence} color={color} />

      {/* Chat with this agent button */}
      {onChat && (
        <Pressable
          onPress={() => onChat(agent)}
          style={[styles.chatBtn, { borderColor: color + '55' }]}
        >
          <Text style={[styles.chatBtnText, { color }]}>💬 Chat with {name}</Text>
        </Pressable>
      )}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderRadius: 16,
    padding: 16,
    gap: 12,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarEmoji: {
    fontSize: 20,
  },
  agentMeta: {
    flex: 1,
    gap: 2,
  },
  agentName: {
    fontSize: 14,
    fontWeight: '700',
  },
  agentRole: {
    color: colors.textSecondary,
    fontSize: 11,
  },
  noteChip: {
    backgroundColor: '#1A0A2E',
    borderWidth: 1,
    borderColor: 'rgba(195,166,255,0.3)',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
    alignSelf: 'flex-start',
  },
  noteChipText: {
    color: '#C3A6FF',
    fontSize: 11,
    fontWeight: '500',
  },
  summary: {
    color: colors.textPrimary,
    fontSize: 13,
    lineHeight: 19,
  },
  flagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  flagChip: {
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  flagText: {
    color: colors.textSecondary,
    fontSize: 11,
  },
  chatBtn: {
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.04)',
  },
  chatBtnText: {
    fontSize: 13,
    fontWeight: '700',
  },
});

const mdStyles = {
  body: {
    color: colors.textPrimary,
    fontSize: 13,
    lineHeight: 19,
  },
  strong: {
    fontWeight: '700',
    color: colors.textPrimary,
  },
  em: {
    fontStyle: 'italic',
    color: colors.textPrimary,
  },
  bullet_list: {
    marginVertical: 4,
  },
  ordered_list: {
    marginVertical: 4,
  },
  list_item: {
    marginVertical: 2,
  },
  bullet_list_icon: {
    color: colors.textSecondary,
    fontSize: 13,
    lineHeight: 19,
    marginRight: 6,
  },
  heading1: {
    color: colors.textPrimary,
    fontSize: 15,
    fontWeight: '700',
    marginVertical: 4,
  },
  heading2: {
    color: colors.textPrimary,
    fontSize: 14,
    fontWeight: '700',
    marginVertical: 3,
  },
  heading3: {
    color: colors.textPrimary,
    fontSize: 13,
    fontWeight: '700',
    marginVertical: 2,
  },
  paragraph: {
    marginVertical: 2,
  },
  code_inline: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    color: colors.textPrimary,
    fontSize: 12,
    borderRadius: 4,
    paddingHorizontal: 4,
  },
  fence: {
    backgroundColor: 'rgba(255,255,255,0.06)',
    color: colors.textPrimary,
    fontSize: 12,
    borderRadius: 8,
    padding: 8,
    marginVertical: 4,
  },
  link: {
    color: '#6C9CFF',
  },
};
