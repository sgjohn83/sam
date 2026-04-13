import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { StatusBadge } from '../ui/StatusBadge';
import { Card } from '../ui/Card';
import { colors, spacing, typography } from '../../theme';

export function StudentCard({ student }) {
  const navigation = useNavigation();

  return (
    <Card style={styles.container}>
      <TouchableOpacity
        style={styles.card}
        onPress={() => navigation.navigate('StudentDetail', { studentId: student.id })}
      >
        <View style={styles.header}>
          <Text style={styles.name} numberOfLines={1}>{student.full_name}</Text>
          <StatusBadge status={student.status} />
        </View>
        
        <Text style={styles.email}>{student.email}</Text>
        
        <View style={styles.footer}>
          {student.application_number ? (
            <Text style={styles.appNumber}>#{student.application_number}</Text>
          ) : (
            <Text style={styles.noApp}>No application yet</Text>
          )}
          
          {student.branch_name && (
            <View style={styles.branchContainer}>
              <View style={styles.dot} />
              <Text style={styles.branch} numberOfLines={1}>{student.branch_name}</Text>
            </View>
          )}
        </View>
      </TouchableOpacity>
    </Card>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: spacing.md,
    marginVertical: 4,
    padding: 0,
    overflow: 'hidden',
  },
  card: {
    padding: spacing.md,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  name: {
    ...typography.h4,
    fontWeight: '800',
    color: colors.text,
    flex: 1,
    marginRight: spacing.sm,
  },
  email: {
    fontSize: 13,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  appNumber: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.primary,
    backgroundColor: colors.primary + '10',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  noApp: {
    fontSize: 11,
    color: '#94A3B8',
    fontStyle: 'italic',
  },
  branchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginLeft: spacing.sm,
  },
  dot: {
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: '#CBD5E1',
    marginRight: spacing.sm,
  },
  branch: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '600',
  },
});
