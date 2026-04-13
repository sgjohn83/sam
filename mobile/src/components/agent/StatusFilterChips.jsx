import React from 'react';
import { ScrollView, TouchableOpacity, Text, StyleSheet, View } from 'react-native';
import { colors, spacing } from '../../theme';

const STATUS_OPTIONS = [
  { value: '', label: 'All', color: '#6B7280' },
  { value: 'draft', label: 'Draft', color: '#9CA3AF' },
  { value: 'submitted', label: 'Submitted', color: '#3B82F6' },
  { value: 'under_verification', label: 'Verifying', color: '#F59E0B' },
  { value: 'verified', label: 'Verified', color: '#10B981' },
  { value: 'seat_allocated', label: 'Seat', color: '#8B5CF6' },
  { value: 'fee_pending', label: 'Fee Due', color: '#F97316' },
  { value: 'admitted', label: 'Admitted', color: '#059669' },
  { value: 'rejected', label: 'Rejected', color: '#EF4444' },
];

export function StatusFilterChips({ selected, onSelect }) {
  return (
    <View style={styles.wrapper}>
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false} 
        style={styles.container}
        contentContainerStyle={styles.content}
      >
        {STATUS_OPTIONS.map((status) => {
          const isSelected = selected === status.value;
          return (
            <TouchableOpacity
              key={status.label}
              style={[
                styles.chip, 
                isSelected ? { backgroundColor: status.color } : { backgroundColor: '#F1F5F9' }
              ]}
              onPress={() => onSelect(status.value)}
            >
              <Text style={[
                styles.label, 
                isSelected ? styles.selectedLabel : { color: '#64748B' }
              ]}>
                {status.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  container: {
    paddingVertical: 12,
  },
  content: {
    paddingHorizontal: spacing.md,
    alignItems: 'center',
    gap: 8,
  },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  label: {
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  selectedLabel: {
    color: '#fff',
  },
});
