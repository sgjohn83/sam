import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const STATUS_CONFIG = {
  draft: { label: 'Draft', color: '#6B7280', bg: '#F3F4F6' },
  submitted: { label: 'Submitted', color: '#1D4ED8', bg: '#EFF6FF' },
  under_verification: { label: 'Verifying', color: '#B45309', bg: '#FFFBEB' },
  verified: { label: 'Verified', color: '#047857', bg: '#ECFDF5' },
  seat_allocated: { label: 'Seat', color: '#6D28D9', bg: '#F5F3FF' },
  fee_pending: { label: 'Fee Due', color: '#C2410C', bg: '#FFF7ED' },
  admitted: { label: 'Admitted', color: '#065F46', bg: '#ECFDF5' },
  rejected: { label: 'Rejected', color: '#B91C1C', bg: '#FEF2F2' },
};

export function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || { label: status, color: '#6B7280', bg: '#F3F4F6' };

  return (
    <View style={[styles.badge, { backgroundColor: config.bg }]}>
      <Text style={[styles.text, { color: config.color }]}>{config.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  text: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
});
