import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { Clock, CheckCircle, IndianRupee, XCircle } from 'lucide-react-native';
import { Card } from '../ui/Card';
import { colors, spacing, typography } from '../../theme';

export function CommissionCard({ record }) {
  const statusColors = {
    pending: { bg: '#FEF3C7', text: '#92400E', icon: Clock },
    approved: { bg: '#DBEAFE', text: '#1E40AF', icon: CheckCircle },
    paid: { bg: '#D1FAE5', text: '#065F46', icon: IndianRupee },
    rejected: { bg: '#FEE2E2', text: '#991B1B', icon: XCircle },
  };
  const style = statusColors[record.status] || statusColors.pending;
  const StatusIcon = style.icon;

  return (
    <Card style={styles.container}>
      <View style={styles.topRow}>
        <View style={{ flex: 1 }}>
          <Text style={styles.studentName} numberOfLines={1}>{record.student_name}</Text>
          <Text style={styles.appNumber}>#{record.application_number || 'N/A'}</Text>
        </View>
        <View style={[styles.badge, { backgroundColor: style.bg }]}>
          <StatusIcon size={12} color={style.text} />
          <Text style={[styles.badgeText, { color: style.text }]}>
            {record.status_display}
          </Text>
        </View>
      </View>

      {record.branch_name && <Text style={styles.branch}>{record.branch_name}</Text>}

      <View style={styles.amountRow}>
        <View style={styles.amountItem}>
          <Text style={styles.amountLabel}>Fee</Text>
          <Text style={styles.amountValue}>₹{record.fee_amount}</Text>
        </View>
        <View style={styles.amountItem}>
          <Text style={styles.amountLabel}>Rate</Text>
          <Text style={styles.amountValue}>{record.commission_rate}%</Text>
        </View>
        <View style={[styles.amountItem, { alignItems: 'flex-end' }]}>
          <Text style={styles.amountLabel}>Earnings</Text>
          <Text style={styles.commissionValue}>₹{record.commission_amount}</Text>
        </View>
      </View>

      {record.payment_reference && (
        <View style={styles.footer}>
          <Text style={styles.paymentRef}>Ref: {record.payment_reference}</Text>
          {record.paid_at && (
             <Text style={styles.paymentRef}> • {new Date(record.paid_at).toLocaleDateString()}</Text>
          )}
        </View>
      )}
    </Card>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: spacing.md,
    marginVertical: 4,
    padding: spacing.md,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  studentName: {
    ...typography.h4,
    fontWeight: '800',
    color: colors.text,
  },
  appNumber: {
    fontSize: 11,
    color: '#94A3B8',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginTop: 2,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  branch: {
    fontSize: 13,
    color: colors.primary,
    fontWeight: '600',
    marginTop: 4,
  },
  amountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.md,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  amountItem: {
    flex: 1,
  },
  amountLabel: {
    fontSize: 10,
    color: '#94A3B8',
    textTransform: 'uppercase',
    fontWeight: '700',
    marginBottom: 2,
  },
  amountValue: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
  },
  commissionValue: {
    fontSize: 15,
    fontWeight: '900',
    color: '#059669',
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.sm,
    paddingTop: spacing.xs,
  },
  paymentRef: {
    fontSize: 11,
    color: '#94A3B8',
    fontWeight: '600',
  },
});
