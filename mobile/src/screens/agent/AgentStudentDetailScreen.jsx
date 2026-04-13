import React from 'react';
import { ScrollView, View, Text, StyleSheet, Linking, TouchableOpacity } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useRoute } from '@react-navigation/native';
import { Phone, Mail, Award, FileText, Smartphone, LayoutGrid } from 'lucide-react-native';
import { agentApi } from '../../services/agentApi';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { StatusTimeline } from '../../components/agent/StatusTimeline';
import LoadingScreen from '../../components/ui/LoadingScreen';
import { Card } from '../../components/ui/Card';
import { colors, spacing, typography } from '../../theme';

export function AgentStudentDetailScreen() {
  const route = useRoute();
  const { studentId } = route.params;

  const { data: student, isLoading } = useQuery({
    queryKey: ['agent-student', studentId],
    queryFn: () => agentApi.getStudentDetail(studentId).then(r => r.data),
  });

  if (isLoading) return <LoadingScreen />;
  if (!student) return <View style={styles.error}><Text>Student not found</Text></View>;

  return (
    <ScrollView style={styles.container}>
      {/* Header Info */}
      <View style={styles.header}>
        <View style={styles.nameRow}>
          <Text style={styles.name}>{student.full_name}</Text>
          <StatusBadge status={student.status} />
        </View>
        <Text style={styles.appId}>Application ID: {student.application_number || 'Pending'}</Text>
        
        <View style={styles.contactRow}>
          <TouchableOpacity style={styles.contactItem} onPress={() => Linking.openURL(`mailto:${student.email}`)}>
            <Mail size={16} color={colors.primary} />
            <Text style={styles.contactText}>{student.email}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.contactItem} onPress={() => Linking.openURL(`tel:${student.mobile_number}`)}>
            <Phone size={16} color={colors.primary} />
            <Text style={styles.contactText}>{student.mobile_number}</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Allocation & Academic */}
      {(student.branch_name || student.category) && (
        <Card style={styles.section}>
          <Text style={styles.sectionTitle}>Course & Quota</Text>
          <View style={styles.infoGrid}>
            <View style={styles.infoBox}>
              <LayoutGrid size={18} color="#94A3B8" />
              <View>
                <Text style={styles.infoLabel}>Allocated Branch</Text>
                <Text style={styles.infoValue}>{student.branch_name || 'Not Allocated'}</Text>
              </View>
            </View>
            <View style={styles.infoBox}>
              <Award size={18} color="#94A3B8" />
              <View>
                <Text style={styles.infoLabel}>Category/Quota</Text>
                <Text style={styles.infoValue}>{student.category || 'General'}</Text>
              </View>
            </View>
          </View>
        </Card>
      )}

      {/* Commission Info */}
      {student.commission_record && (
        <Card style={styles.section}>
          <Text style={styles.sectionTitle}>Earnings Detail</Text>
          <View style={styles.commissionRow}>
            <View>
              <Text style={styles.infoLabel}>Commission Amount</Text>
              <Text style={styles.earningsValue}>₹{student.commission_record.commission_amount}</Text>
            </View>
            <View style={[styles.payoutBadge, { backgroundColor: student.commission_record.status === 'paid' ? '#ECFDF5' : '#F1F5F9' }]}>
               <Text style={[styles.payoutText, { color: student.commission_record.status === 'paid' ? '#059669' : '#64748B' }]}>
                 {student.commission_record.status_display}
               </Text>
            </View>
          </View>
          {student.commission_record.payment_reference && (
             <Text style={styles.paymentRef}>Ref: {student.commission_record.payment_reference}</Text>
          )}
        </Card>
      )}

      {/* Status Timeline */}
      <StatusTimeline timeline={student.status_timeline} />

      {/* Document Status */}
      <View style={styles.section}>
          <Text style={[styles.sectionTitle, { marginLeft: spacing.md }]}>Documents & OCR Confidence</Text>
          {student.documents?.map((doc, idx) => (
            <Card key={idx} style={styles.docCard}>
                <View style={styles.docInfo}>
                    <FileText size={20} color={colors.textSecondary} />
                    <View style={{ flex: 1, marginLeft: 12 }}>
                        <Text style={styles.docType}>{doc.type.replace(/_/g, ' ')}</Text>
                        <Text style={styles.docStatus}>{doc.status}</Text>
                    </View>
                    {doc.confidence !== null && (
                        <View style={[styles.confidenceBadge, { backgroundColor: doc.confidence > 0.8 ? '#ECFDF5' : '#FEF2F2' }]}>
                            <Text style={[styles.confidenceText, { color: doc.confidence > 0.8 ? '#059669' : '#EF4444' }]}>
                                {Math.round(doc.confidence * 100)}% Match
                            </Text>
                        </View>
                    )}
                </View>
            </Card>
          ))}
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    backgroundColor: colors.white,
    padding: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  nameRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: spacing.sm,
  },
  name: {
    ...typography.h3,
    fontWeight: '900',
    color: colors.text,
    flex: 1,
  },
  appId: {
    fontSize: 12,
    color: colors.textSecondary,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginTop: 4,
  },
  contactRow: {
    marginTop: spacing.md,
    gap: spacing.sm,
  },
  contactItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  contactText: {
    fontSize: 14,
    color: colors.primary,
    textDecorationLine: 'underline',
  },
  section: {
    marginTop: spacing.sm,
    padding: spacing.md,
    marginHorizontal: spacing.sm,
    backgroundColor: 'transparent',
    borderWidth: 0,
    shadowOpacity: 0,
  },
  docCard: {
      backgroundColor: '#fff',
      marginHorizontal: spacing.sm,
      marginBottom: 8,
      padding: spacing.md,
  },
  sectionTitle: {
    ...typography.h5,
    fontWeight: '800',
    color: '#1E293B',
    marginBottom: spacing.md,
  },
  infoGrid: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  infoBox: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#fff',
    padding: spacing.md,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  infoLabel: {
    fontSize: 10,
    color: '#94A3B8',
    textTransform: 'uppercase',
    fontWeight: '700',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
  },
  commissionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: spacing.md,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  earningsValue: {
    fontSize: 22,
    fontWeight: '900',
    color: '#059669',
  },
  payoutBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  payoutText: {
    fontSize: 11,
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
  paymentRef: {
     fontSize: 11,
     color: '#94A3B8',
     marginTop: 8,
     textAlign: 'right',
  },
  docInfo: {
      flexDirection: 'row',
      alignItems: 'center',
  },
  docType: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
    textTransform: 'capitalize',
  },
  docStatus: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  confidenceBadge: {
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 6,
  },
  confidenceText: {
      fontSize: 10,
      fontWeight: 'bold',
  },
  error: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
  }
});
