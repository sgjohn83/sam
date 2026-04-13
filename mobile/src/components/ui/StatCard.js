import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Card } from './Card';
import { colors, spacing, typography } from '../../theme';

export const StatCard = ({ title, value, icon: Icon, color, onPress }) => {
  const CardWrapper = onPress ? TouchableOpacity : View;

  return (
    <CardWrapper onPress={onPress} style={styles.container}>
      <Card style={styles.card}>
        <View style={[styles.iconContainer, { backgroundColor: color + '15' }]}>
          <Icon size={24} color={color} />
        </View>
        <Text style={styles.value}>{value}</Text>
        <Text style={styles.title}>{title}</Text>
      </Card>
    </CardWrapper>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: spacing.xs,
  },
  card: {
    padding: spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 110,
  },
  iconContainer: {
    padding: spacing.sm,
    borderRadius: 12,
    marginBottom: spacing.xs,
  },
  value: {
    ...typography.h3,
    color: colors.text,
    fontWeight: 'bold',
  },
  title: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
});
