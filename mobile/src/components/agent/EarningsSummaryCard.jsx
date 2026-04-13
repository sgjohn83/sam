import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing, typography } from '../../theme';

export function EarningsSummaryCard({ summary }) {
  const months = summary?.monthly_earnings?.slice(0, 6)?.reverse() || [];
  const maxAmount = Math.max(...months.map(m => parseFloat(m.total)), 1);

  return (
    <View style={styles.card}>
      <View style={styles.topSection}>
        <Text style={styles.lifetimeLabel}>Lifetime Earnings</Text>
        <Text style={styles.lifetimeValue}>₹{summary.lifetime.total_earned}</Text>
        <Text style={styles.lifetimeStudents}>
          {summary.lifetime.total_students} students successfully admitted
        </Text>
      </View>

      {months.length > 0 && (
        <View style={styles.chartContainer}>
          {months.map((m) => {
            const barHeightPercent = (parseFloat(m.total) / maxAmount) * 100;
            return (
              <View key={m.month} style={styles.barColumn}>
                <View style={styles.barTrack}>
                  <View
                    style={[
                      styles.bar,
                      { height: `${Math.max(barHeightPercent, 4)}%` },
                    ]}
                  />
                </View>
                <Text style={styles.barLabel}>{m.month_label.split(' ')[0]}</Text>
              </View>
            );
          })}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.primary,
    margin: spacing.md,
    borderRadius: 20,
    padding: spacing.lg,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  topSection: {
    marginBottom: spacing.xl,
  },
  lifetimeLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.7)',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  lifetimeValue: {
    fontSize: 34,
    fontWeight: '900',
    color: '#fff',
    marginTop: 4,
  },
  lifetimeStudents: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.85)',
    fontWeight: '500',
    marginTop: 4,
  },
  chartContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    paddingTop: spacing.md,
    height: 100,
  },
  barColumn: {
    flex: 1,
    alignItems: 'center',
    gap: 8,
  },
  barTrack: {
    flex: 1,
    width: 14,
    justifyContent: 'flex-end',
  },
  bar: {
    width: '100%',
    backgroundColor: '#fff',
    borderRadius: 7,
    opacity: 0.9,
  },
  barLabel: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.7)',
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
});
