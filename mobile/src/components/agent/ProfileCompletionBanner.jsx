import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors, spacing, typography } from '../../theme';

export function ProfileCompletionBanner({ completion, onPress }) {
  return (
    <TouchableOpacity style={styles.banner} onPress={onPress}>
      <View style={styles.row}>
          <Text style={styles.text}>
            Profile {completion.percentage}% complete
          </Text>
          <Text style={styles.stepCounter}>
              {completion.completed}/{completion.total} steps
          </Text>
      </View>
      
      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width: `${completion.percentage}%` }]} />
      </View>
      
      {!completion.can_register_students && (
          <View style={styles.hintContainer}>
            <View style={styles.dot} />
            <Text style={styles.hint}>Complete all steps to start registering students</Text>
          </View>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: colors.primary + '10',
    margin: spacing.md,
    borderRadius: 16,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.primary + '20',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  text: {
    ...typography.body,
    fontWeight: '800',
    color: colors.primary,
  },
  stepCounter: {
      fontSize: 12,
      color: colors.primary,
      fontWeight: '600',
      opacity: 0.7,
  },
  progressTrack: {
    height: 8,
    backgroundColor: colors.white,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 4,
  },
  hintContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      marginTop: spacing.sm,
      gap: 6,
  },
  dot: {
      width: 4,
      height: 4,
      borderRadius: 2,
      backgroundColor: colors.primary,
  },
  hint: {
    fontSize: 11,
    color: colors.primary,
    fontWeight: '600',
    opacity: 0.8,
  },
});
