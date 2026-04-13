import React, { useState } from 'react';
import { View, FlatList, TextInput, RefreshControl, StyleSheet } from 'react-native';
import { useInfiniteQuery } from '@tanstack/react-query';
import { agentApi } from '../../services/agentApi';
import { StatusFilterChips } from '../../components/agent/StatusFilterChips';
import { StudentCard } from '../../components/agent/StudentCard';
import { useDebounce } from '../../hooks/useDebounce';
import EmptyState from '../../components/ui/EmptyState';
import { colors, spacing } from '../../theme';

export function AgentStudentListScreen() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const debouncedSearch = useDebounce(search, 300);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isLoading,
    refetch,
    isRefetching,
  } = useInfiniteQuery({
    queryKey: ['agent-students', debouncedSearch, statusFilter],
    queryFn: ({ pageParam = 1 }) =>
      agentApi.getStudents({
        search: debouncedSearch,
        status: statusFilter,
        page: pageParam,
      }).then(r => r.data),
    initialPageParam: 1,
    getNextPageParam: (lastPage) =>
      lastPage.next ? (new URL(lastPage.next).searchParams.get('page')) : undefined,
  });

  const students = data?.pages?.flatMap(p => p.results) || [];

  return (
    <View style={styles.container}>
      {/* Search bar */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name, email, or app #..."
          placeholderTextColor="#94A3B8"
          value={search}
          onChangeText={setSearch}
        />
      </View>

      {/* Status filter chips */}
      <StatusFilterChips
        selected={statusFilter}
        onSelect={setStatusFilter}
      />

      {/* Student list */}
      <FlatList
        data={students}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => <StudentCard student={item} />}
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
        onEndReached={() => hasNextPage && fetchNextPage()}
        onEndReachedThreshold={0.5}
        ListEmptyComponent={<EmptyState message="No students found" />}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  searchContainer: {
    padding: spacing.md,
    backgroundColor: '#fff',
  },
  searchInput: {
    height: 48,
    backgroundColor: '#F1F5F9',
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 14,
    color: colors.text,
  },
  listContent: {
    paddingVertical: spacing.sm,
    paddingBottom: spacing.xl,
  },
});
