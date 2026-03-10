import React from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { colors } from '../constants/colors';

export default function SubmissionCard({ image, healthNote, timestamp, compact }) {
  const thumbSize = compact ? 52 : 68;

  return (
    <View style={styles.card}>
      <View style={styles.row}>
        {/* Thumbnail */}
        {image ? (
          <Image
            source={{ uri: image }}
            style={[styles.thumb, { width: thumbSize, height: thumbSize, borderRadius: thumbSize * 0.2 }]}
          />
        ) : (
          <View style={[styles.thumbPlaceholder, { width: thumbSize, height: thumbSize, borderRadius: thumbSize * 0.2 }]}>
            <Text style={styles.thumbEmoji}>🍪</Text>
          </View>
        )}

        {/* Meta */}
        <View style={styles.meta}>
          <Text style={styles.label}>YOUR SCAN · {timestamp ?? '—'}</Text>

          {healthNote ? (
            <View style={styles.noteChip}>
              <Text style={styles.noteText} numberOfLines={2}>
                📝 "{healthNote}"
              </Text>
            </View>
          ) : (
            <Text style={styles.noNote}>No health note added</Text>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    padding: 14,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  thumb: {
    resizeMode: 'cover',
  },
  thumbPlaceholder: {
    backgroundColor: '#1A1A2E',
    alignItems: 'center',
    justifyContent: 'center',
  },
  thumbEmoji: {
    fontSize: 24,
  },
  meta: {
    flex: 1,
    gap: 8,
    justifyContent: 'center',
  },
  label: {
    color: colors.cyan,
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.5,
    textTransform: 'uppercase',
  },
  noteChip: {
    backgroundColor: '#1A0A2E',
    borderWidth: 1,
    borderColor: 'rgba(195,166,255,0.3)',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    alignSelf: 'flex-start',
  },
  noteText: {
    color: '#C3A6FF',
    fontSize: 12,
    lineHeight: 17,
  },
  noNote: {
    color: colors.textSecondary,
    fontSize: 12,
  },
});
