import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { CheckCircle2, Circle } from 'lucide-react-native';
import { colors, spacing, typography } from '../../theme';

export function StatusTimeline({ timeline }) {
  if (!timeline || timeline.length === 0) return null;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Application Journey</Text>
      <View style={styles.timeline}>
        {timeline.map((step, index) => {
          const isLast = index === timeline.length - 1;
          return (
            <View key={index} style={styles.step}>
              <View style={styles.indicatorContainer}>
                <View style={[styles.dot, isLast ? styles.activeDot : styles.pastDot]}>
                   {isLast ? <CheckCircle2 size={16} color={colors.primary} /> : <View style={styles.innerDot} />}
                </View>
                {!isLast && <View style={styles.line} />}
              </View>
              <View style={styles.content}>
                <Text style={[styles.status, isLast && styles.activeStatus]}>
                    {step.status.replace(/_/g, ' ')}
                </Text>
                <Text style={styles.timestamp}>
                    {new Date(step.timestamp).toLocaleDateString()} {new Date(step.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </Text>
              </View>
            </View>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: spacing.md,
    backgroundColor: '#fff',
    marginTop: spacing.sm,
  },
  title: {
    ...typography.h4,
    fontWeight: 'bold',
    marginBottom: spacing.md,
  },
  timeline: {
    paddingLeft: spacing.xs,
  },
  step: {
    flexDirection: 'row',
    minHeight: 60,
  },
  indicatorContainer: {
    alignItems: 'center',
    width: 20,
    marginRight: spacing.md,
  },
  dot: {
    width: 20,
    height: 20,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1,
  },
  activeDot: {
    backgroundColor: '#fff',
  },
  pastDot: {
    backgroundColor: '#E2E8F0',
    width: 10,
    height: 10,
    marginTop: 5,
  },
  innerDot: {
    backgroundColor: '#94A3B8',
    width: 4,
    height: 4,
    borderRadius: 2,
  },
  line: {
    flex: 1,
    width: 2,
    backgroundColor: '#E2E8F0',
    marginVertical: -2,
  },
  content: {
    flex: 1,
    paddingBottom: spacing.md,
  },
  status: {
    fontSize: 14,
    fontWeight: '600',
    color: '#64748B',
    textTransform: 'capitalize',
  },
  activeStatus: {
    color: colors.text,
    fontWeight: '700',
  },
  timestamp: {
    fontSize: 11,
    color: '#94A3B8',
    marginTop: 2,
  },
});
