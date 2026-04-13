import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Card } from '../ui/Card';
import { colors, spacing, typography } from '../../theme';

export function PipelineFunnel({ data, total }) {
  const maxCount = Math.max(...Object.values(data), 1);
  const stages = [
    { key: 'draft', label: 'Draft', color: '#9CA3AF' },
    { key: 'submitted', label: 'Submitted', color: '#3B82F6' },
    { key: 'under_verification', label: 'Verifying', color: '#F59E0B' },
    { key: 'verified', label: 'Verified', color: '#10B981' },
    { key: 'seat_allocated', label: 'Seat Alloc.', color: '#8B5CF6' },
    { key: 'fee_pending', label: 'Fee Due', color: '#F97316' },
    { key: 'admitted', label: 'Admitted', color: '#059669' },
    { key: 'rejected', label: 'Rejected', color: '#EF4444' },
  ];

  return (
    <Card style={styles.container}>
      <Text style={styles.title}>Application Pipeline ({total})</Text>
      <View style={styles.funnel}>
        {stages.map((stage) => {
          const count = data[stage.key] || 0;
          const widthPercent = (count / maxCount) * 100;
          
          return (
            <View key={stage.key} style={styles.row}>
              <View style={styles.labelContainer}>
                <Text style={styles.label}>{stage.label}</Text>
              </View>
              <View style={styles.barTrack}>
                <View
                  style={[
                    styles.barFill,
                    {
                      width: `${Math.max(widthPercent, 1)}%`,
                      backgroundColor: stage.color,
                      opacity: count > 0 ? 1 : 0.2,
                    },
                  ]}
                />
              </View>
              <View style={styles.countContainer}>
                <Text style={[styles.count, count > 0 && { color: colors.text, fontWeight: '700' }]}>
                    {count}
                </Text>
              </View>
            </View>
          );
        })}
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  container: {
    margin: spacing.md,
    padding: spacing.md,
  },
  title: {
    ...typography.h4,
    fontWeight: '900',
    color: colors.text,
    marginBottom: spacing.lg,
  },
  funnel: {
    gap: 12,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  labelContainer: {
    width: 75,
  },
  label: {
    fontSize: 10,
    fontWeight: '800',
    color: '#64748B',
    textTransform: 'uppercase',
  },
  barTrack: {
    flex: 1,
    height: 10,
    backgroundColor: '#F1F5F9',
    borderRadius: 5,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 5,
  },
  countContainer: {
    width: 24,
    alignItems: 'flex-end',
  },
  count: {
    fontSize: 12,
    color: '#94A3B8',
    fontWeight: '400',
  },
});
