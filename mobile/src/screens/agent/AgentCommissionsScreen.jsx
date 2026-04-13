import React, { useState } from 'react';
import { View, FlatList, RefreshControl, StyleSheet } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { agentApi } from '../../services/agentApi';
import { CommissionCard } from '../../components/agent/CommissionCard';
import { EarningsSummaryCard } from '../../components/agent/EarningsSummaryCard';
import { CommissionFilterChips } from '../../components/agent/CommissionFilterChips';
import EmptyState from '../../components/ui/EmptyState';
import LoadingScreen from '../../components/ui/LoadingScreen';
import { spacing } from '../../theme';

export function AgentCommissionsScreen({ route }) {
  const initialFilter = route.params?.filter || '';
  const [statusFilter, setStatusFilter] = useState(initialFilter);

  const { data: summary } = useQuery({
    queryKey: ['agent-commission-summary'],
    queryFn: () => agentApi.getCommissionSummary().then(r => r.data),
  });

  const { data: commissions, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['agent-commissions', statusFilter],
    queryFn: () => agentApi.getCommissions({ status: statusFilter }).then(r => r.data),
  });

  if (isLoading) return <LoadingScreen />;

  const records = commissions?.results || [];

  return (
    <View style={styles.container}>
      <FlatList
        data={records}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => <CommissionCard record={item} />}
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
        ListHeaderComponent={
          <View style={styles.header}>
            {/* Earnings summary */}
            {summary && <EarningsSummaryCard summary={summary} />}
            {/* Filter chips */}
            <CommissionFilterChips selected={statusFilter} onSelect={setStatusFilter} />
          </View>
        }
        ListEmptyComponent={<EmptyState message="No commission records found" />}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    paddingBottom: spacing.sm,
  },
  listContent: {
    paddingBottom: spacing.xl,
  },
});
