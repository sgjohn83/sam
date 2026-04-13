import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { colors, spacing } from '../../theme';

const CATEGORIES = [
  { label: 'General', value: 'general' },
  { label: 'OBC', value: 'obc' },
  { label: 'SC', value: 'sc' },
  { label: 'ST', value: 'st' },
];

export function CategoryPicker({ value, onChange }) {
  return (
    <View style={styles.container}>
      {CATEGORIES.map((cat) => {
        const isSelected = value === cat.value;
        return (
          <TouchableOpacity
            key={cat.value}
            style={[styles.chip, isSelected && styles.selectedChip]}
            onPress={() => onChange(cat.value)}
          >
            <Text style={[styles.label, isSelected && styles.selectedLabel]}>
              {cat.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 4,
  },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  selectedChip: {
    backgroundColor: colors.primary + '15',
    borderColor: colors.primary,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#64748B',
  },
  selectedLabel: {
    color: colors.primary,
  },
});
