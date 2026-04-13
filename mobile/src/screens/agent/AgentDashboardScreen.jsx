import React from 'react';
import { ScrollView, View, Text, TouchableOpacity, RefreshControl, StyleSheet } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { Users, GraduationCap, Clock, IndianRupee, AlertTriangle, CheckCircle2, ArrowRight } from 'lucide-react-native';
import { agentApi } from '../../services/agentApi';
import { StatCard } from '../../components/ui/StatCard';
import { PipelineFunnel } from '../../components/agent/PipelineFunnel';
import { ProfileCompletionBanner } from '../../components/agent/ProfileCompletionBanner';
import LoadingScreen from '../../components/ui/LoadingScreen';
import { colors, spacing, typography } from '../../theme';

export function AgentDashboardScreen() {
  const navigation = useNavigation();

  const { 
    data: dashboard, 
    isLoading, 
    refetch, 
    isRefetching,
    dataUpdatedAt: dashboardUpdatedAt,
    isError: isDashboardError
  } = useQuery({
    queryKey: ['agent-dashboard'],
    queryFn: () => agentApi.getDashboard().then(r => r.data),
  });

  const { data: completion } = useQuery({
    queryKey: ['agent-completion'],
    queryFn: () => agentApi.getCompletionStatus().then(r => r.data),
  });

  const { data: pipeline } = useQuery({
    queryKey: ['agent-pipeline'],
    queryFn: () => agentApi.getPipelineSummary().then(r => r.data),
    refetchInterval: 120 * 1000, 
  });

  if (isLoading) return <LoadingScreen />;

  const hasStudents = dashboard?.students?.total_referred > 0;
  const lastUpdated = dashboardUpdatedAt ? new Date(dashboardUpdatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : null;

  return (
    <View style={{ flex: 1 }}>
      {/* Offline/Cached Banner */}
      {isDashboardError && (
          <View style={styles.offlineBanner}>
              <Text style={styles.offlineText}>You are currently offline. Showing cached data from {lastUpdated}</Text>
          </View>
      )}

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Welcome back,</Text>
            <Text style={styles.agencyName}>{dashboard?.agent?.agency_name || 'Partner Agent'}</Text>
          </View>
          {lastUpdated && !isDashboardError && (
              <Text style={styles.syncStatus}>Last synced: {lastUpdated}</Text>
          )}
        </View>

        {/* Profile completion banner if incomplete */}
        {completion && completion.percentage < 100 && (
          <ProfileCompletionBanner
            completion={completion}
            onPress={() => navigation.navigate('Profile')}
          />
        )}

        {/* Empty State Onboarding (Edge Case 1) */}
        {!hasStudents && (
          <View style={styles.onboardingCard}>
             <Text style={styles.onboardingTitle}>Get Started in 3 Steps</Text>
             <View style={styles.steps}>
                <OnboardingStep 
                    number={1} 
                    text="Complete your bank and identity details" 
                    done={completion?.percentage >= 75} 
                    onPress={() => navigation.navigate('Profile')}
                />
                <OnboardingStep 
                    number={2} 
                    text="Wait for administrative verification" 
                    done={dashboard?.agent?.is_verified} 
                />
                <OnboardingStep 
                    number={3} 
                    text="Register your first student to start earning" 
                    done={false}
                    onPress={dashboard?.agent?.is_verified ? () => navigation.navigate('Register') : null}
                />
             </View>
          </View>
        )}

        {/* Verification status warning */}
        {dashboard?.agent && !dashboard.agent.is_verified && (
          <View style={styles.warningBanner}>
            <AlertTriangle size={20} color="#92400E" />
            <Text style={styles.warningText}>
              Account pending verification. Student registration will be enabled once verified.
            </Text>
          </View>
        )}

        {/* Stat cards — 2x2 grid */}
        <View style={styles.gridContainer}>
          <View style={styles.row}>
            <StatCard
              title="Students"
              value={dashboard?.students?.total_referred || 0}
              icon={Users}
              color="#2563EB"
              onPress={() => navigation.navigate('Students')}
            />
            <StatCard
              title="Admitted"
              value={dashboard?.students?.admitted || 0}
              icon={GraduationCap}
              color="#059669"
            />
          </View>
          <View style={styles.row}>
            <StatCard
              title="Pending"
              value={`₹${dashboard?.commission?.pending_amount || 0}`}
              icon={Clock}
              color="#D97706"
              onPress={() => navigation.navigate('Commissions', { filter: 'pending' })}
            />
            <StatCard
              title="Earned"
              value={`₹${dashboard?.commission?.paid_amount || 0}`}
              icon={IndianRupee}
              color="#059669"
              onPress={() => navigation.navigate('Commissions', { filter: 'paid' })}
            />
          </View>
        </View>

        {/* Pipeline funnel */}
        {hasStudents && pipeline && (
          <PipelineFunnel data={pipeline.pipeline} total={pipeline.total} />
        )}

        {/* Quick action: Register student */}
        {dashboard?.agent?.is_verified && (
          <TouchableOpacity
            style={styles.registerCta}
            onPress={() => navigation.navigate('Register')}
          >
            <Text style={styles.registerCtaText}>+ Register New Student</Text>
          </TouchableOpacity>
        )}
        
        <View style={{ height: spacing.xl }} />
      </ScrollView>
    </View>
  );
}

const OnboardingStep = ({ number, text, done, onPress }) => (
    <TouchableOpacity 
        style={[styles.stepRow, !onPress && { opacity: 0.8 }]} 
        onPress={onPress} 
        disabled={!onPress}
    >
        <View style={[styles.stepCircle, done && styles.stepCircleDone]}>
            {done ? <CheckCircle2 size={16} color="#fff" /> : <Text style={styles.stepNumber}>{number}</Text>}
        </View>
        <Text style={[styles.stepText, done && styles.stepTextDone]}>{text}</Text>
        {onPress && !done && <ArrowRight size={16} color={colors.primary} />}
    </TouchableOpacity>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  content: {
    paddingBottom: spacing.xl,
  },
  offlineBanner: {
    backgroundColor: '#334155',
    padding: 8,
    alignItems: 'center',
  },
  offlineText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
  },
  header: {
    padding: spacing.md,
    paddingTop: spacing.lg,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  greeting: {
    ...typography.caption,
    color: colors.textSecondary,
    fontSize: 12,
  },
  agencyName: {
    ...typography.h3,
    fontWeight: '900',
    color: colors.text,
  },
  syncStatus: {
    fontSize: 10,
    color: '#94A3B8',
    marginBottom: 4,
  },
  onboardingCard: {
      backgroundColor: '#fff',
      margin: spacing.md,
      padding: spacing.md,
      borderRadius: 16,
      borderWidth: 1,
      borderColor: '#E2E8F0',
  },
  onboardingTitle: {
      ...typography.h5,
      fontWeight: '800',
      marginBottom: spacing.md,
      color: colors.text,
  },
  steps: {
      gap: 12,
  },
  stepRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 12,
  },
  stepCircle: {
      width: 28,
      height: 28,
      borderRadius: 14,
      backgroundColor: '#F1F5F9',
      justifyContent: 'center',
      alignItems: 'center',
  },
  stepCircleDone: {
      backgroundColor: '#059669',
  },
  stepNumber: {
      fontSize: 12,
      fontWeight: 'bold',
      color: '#64748B',
  },
  stepText: {
      flex: 1,
      fontSize: 14,
      color: colors.text,
      fontWeight: '500',
  },
  stepTextDone: {
      textDecorationLine: 'line-through',
      color: '#94A3B8',
  },
  warningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    margin: spacing.md,
    padding: spacing.md,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#FDE68A',
    gap: spacing.sm,
  },
  warningText: {
    flex: 1,
    color: '#92400E',
    fontSize: 12,
    fontWeight: '600',
  },
  gridContainer: {
    paddingHorizontal: spacing.sm,
    marginTop: spacing.sm,
  },
  row: {
    flexDirection: 'row',
  },
  registerCta: {
    backgroundColor: colors.primary,
    margin: spacing.md,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  registerCtaText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: 'bold',
  },
});
