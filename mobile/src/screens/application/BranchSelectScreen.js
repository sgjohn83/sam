import React, { useEffect, useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Feather } from "@expo/vector-icons";
import DraggableFlatList, { ScaleDecorator } from "react-native-draggable-flatlist";
import Toast from "react-native-toast-message";

import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Spinner from "../../components/ui/Spinner";
import studentApi from "../../services/studentApi";
import { colors, fontSize, spacing } from "../../theme";

const MAX_SELECTION = 5;

const normalizeId = (value) => String(value || "");

const getBranchAvailableTotal = (branch) => {
  if (typeof branch?.total_available === "number") {
    return branch.total_available;
  }

  const seatBuckets = branch?.available_seats;
  if (!seatBuckets || typeof seatBuckets !== "object") {
    return 0;
  }

  return Object.values(seatBuckets).reduce((sum, bucket) => {
    const available = Number(bucket?.available || 0);
    return sum + (Number.isFinite(available) ? available : 0);
  }, 0);
};

const getSeatHealth = (branch) => {
  const available = getBranchAvailableTotal(branch);
  const seatBuckets = branch?.available_seats;

  if (!seatBuckets || typeof seatBuckets !== "object") {
    return { label: `${available} seats available`, color: colors.textSecondary };
  }

  const total = Object.values(seatBuckets).reduce((sum, bucket) => {
    const count = Number(bucket?.total || 0);
    return sum + (Number.isFinite(count) ? count : 0);
  }, 0);

  if (!total) {
    return { label: `${available} seats available`, color: colors.textSecondary };
  }

  const ratio = available / total;
  if (ratio > 0.5) {
    return { label: `${available} seats available`, color: colors.success };
  }
  if (ratio >= 0.2) {
    return { label: `${available} seats available`, color: colors.warning };
  }
  return { label: `${available} seats available`, color: colors.danger };
};

const BranchSelectScreen = ({ navigation }) => {
  const [selectedIds, setSelectedIds] = useState([]);

  const branchesQuery = useQuery({
    queryKey: ["branches"],
    queryFn: async () => {
      const { data } = await studentApi.getBranches();
      return Array.isArray(data) ? data : [];
    },
  });

  const applicationQuery = useQuery({
    queryKey: ["student-application"],
    queryFn: async () => {
      const { data } = await studentApi.getApplication();
      return data || {};
    },
  });

  useEffect(() => {
    if (selectedIds.length > 0) {
      return;
    }

    const preferences = applicationQuery.data?.branch_preferences || [];
    if (!Array.isArray(preferences) || preferences.length === 0) {
      return;
    }

    const normalized = preferences
      .map((item) => (item && typeof item === "object" ? normalizeId(item.id) : normalizeId(item)))
      .filter(Boolean);

    if (normalized.length > 0) {
      setSelectedIds(normalized.slice(0, MAX_SELECTION));
    }
  }, [applicationQuery.data, selectedIds.length]);

  const branchesById = useMemo(() => {
    const map = {};
    (branchesQuery.data || []).forEach((branch) => {
      map[normalizeId(branch.id)] = branch;
    });
    return map;
  }, [branchesQuery.data]);

  const selectedBranches = useMemo(() => {
    return selectedIds
      .map((id) => branchesById[id])
      .filter(Boolean);
  }, [selectedIds, branchesById]);

  const availableBranches = useMemo(() => {
    const selectedSet = new Set(selectedIds);
    return (branchesQuery.data || []).filter((branch) => !selectedSet.has(normalizeId(branch.id)));
  }, [branchesQuery.data, selectedIds]);

  const isLocked =
    Boolean(applicationQuery.data?.status) && applicationQuery.data?.status !== "draft";

  useEffect(() => {
    if (!isLocked) {
      return;
    }
    Toast.show({
      type: "error",
      text1: "Branch preferences cannot be changed after submission",
    });
    navigation.goBack();
  }, [isLocked, navigation]);

  const saveMutation = useMutation({
    mutationFn: (ids) => studentApi.saveBranchPreferences(ids),
    onSuccess: () => {
      Toast.show({ type: "success", text1: "Preferences saved" });
      navigation.goBack();
    },
    onError: (error) => {
      const message =
        error?.response?.data?.error ||
        error?.response?.data?.detail ||
        "Failed to save preferences";
      Toast.show({ type: "error", text1: message });
    },
  });

  const toggleBranch = (branchId) => {
    const id = normalizeId(branchId);
    if (!id) {
      return;
    }

    if (selectedIds.includes(id)) {
      setSelectedIds((prev) => prev.filter((value) => value !== id));
      return;
    }

    if (selectedIds.length >= MAX_SELECTION) {
      Toast.show({
        type: "error",
        text1: "You can select up to 5 branches",
      });
      return;
    }

    setSelectedIds((prev) => [...prev, id]);
  };

  const onSave = () => {
    if (isLocked) {
      Toast.show({
        type: "error",
        text1: "Branch preferences cannot be changed after submission",
      });
      return;
    }
    if (selectedIds.length < 1) {
      Toast.show({
        type: "error",
        text1: "Select at least one branch",
      });
      return;
    }
    saveMutation.mutate(selectedIds);
  };

  if (branchesQuery.isLoading || applicationQuery.isLoading) {
    return <Spinner fullScreen size="large" />;
  }

  const hasQueryError = branchesQuery.isError || applicationQuery.isError;

  return (
    <ScreenWrapper scroll={false}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.headerRow}>
          <Pressable style={styles.backBtn} onPress={() => navigation.goBack()}>
            <Feather name="arrow-left" size={18} color={colors.text} />
            <Text style={styles.backText}>Back</Text>
          </Pressable>
          <Text style={styles.headerTitle}>Select Branch Preferences</Text>
        </View>

        <Text style={styles.subtitle}>Select up to 5 branches in order of priority.</Text>
        <Text style={styles.hintText}>Drag to reorder.</Text>

        {hasQueryError ? (
          <Card style={styles.sectionCard}>
            <Text style={styles.errorText}>Failed to load branches. Pull to refresh and try again.</Text>
            <Button
              title="Retry"
              variant="secondary"
              onPress={() => {
                branchesQuery.refetch();
                applicationQuery.refetch();
              }}
            />
          </Card>
        ) : null}

        {!hasQueryError ? (
          <Card style={styles.sectionCard}>
            {selectedBranches.length === 0 ? (
              <Text style={styles.emptyText}>No branches selected yet.</Text>
            ) : (
              <DraggableFlatList
                data={selectedBranches}
                keyExtractor={(item) => normalizeId(item.id)}
                onDragEnd={({ data }) => {
                  const reorderedIds = data.map((item) => normalizeId(item.id));
                  setSelectedIds(reorderedIds);
                }}
                scrollEnabled={false}
                renderItem={({ item, drag, isActive, getIndex }) => {
                  const seatInfo = getSeatHealth(item);
                  return (
                    <ScaleDecorator>
                      <View style={[styles.selectedRow, isActive && styles.selectedRowActive]}>
                        <View style={styles.rowMain}>
                          <View style={styles.priorityBadge}>
                            <Text style={styles.priorityBadgeText}>{(getIndex?.() || 0) + 1}</Text>
                          </View>
                          <View style={styles.branchInfo}>
                            <Text style={styles.branchTitle}>
                              {item.code} - {item.name}
                            </Text>
                            <Text style={[styles.seatText, { color: seatInfo.color }]}>
                              {seatInfo.label}
                            </Text>
                          </View>
                        </View>
                        <View style={styles.rowActions}>
                          <Pressable
                            style={styles.iconButton}
                            onPress={() => toggleBranch(item.id)}
                          >
                            <Feather name="x-circle" size={18} color={colors.danger} />
                          </Pressable>
                          <Pressable style={styles.iconButton} onLongPress={drag}>
                            <Feather name="menu" size={18} color={colors.textSecondary} />
                          </Pressable>
                        </View>
                      </View>
                    </ScaleDecorator>
                  );
                }}
              />
            )}
          </Card>
        ) : null}

        {!hasQueryError ? (
          <Card style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>Available Branches</Text>
            {availableBranches.length === 0 ? (
              <Text style={styles.emptyText}>All listed branches are selected.</Text>
            ) : (
              availableBranches.map((branch) => {
                const seatInfo = getSeatHealth(branch);
                return (
                  <Pressable
                    key={normalizeId(branch.id)}
                    style={styles.availableRow}
                    onPress={() => toggleBranch(branch.id)}
                  >
                    <View style={styles.rowMain}>
                      <Feather name="square" size={18} color={colors.textSecondary} />
                      <View style={styles.branchInfo}>
                        <Text style={styles.branchTitle}>
                          {branch.code} - {branch.name}
                        </Text>
                        <Text style={[styles.seatText, { color: seatInfo.color }]}>
                          {seatInfo.label}
                        </Text>
                      </View>
                    </View>
                  </Pressable>
                );
              })
            )}
          </Card>
        ) : null}

        <Button
          title={`Save Preferences (${selectedIds.length} selected)`}
          onPress={onSave}
          loading={saveMutation.isPending}
          disabled={hasQueryError || isLocked}
        />
      </ScrollView>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.sm,
  },
  backBtn: {
    flexDirection: "row",
    alignItems: "center",
    marginRight: spacing.sm,
  },
  backText: {
    marginLeft: spacing.xs,
    color: colors.text,
    fontWeight: "600",
  },
  headerTitle: {
    flex: 1,
    color: colors.text,
    fontSize: fontSize.xl,
    fontWeight: "700",
  },
  subtitle: {
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  hintText: {
    color: colors.textSecondary,
    marginBottom: spacing.md,
    fontSize: fontSize.sm,
  },
  sectionCard: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    color: colors.text,
    fontWeight: "700",
    marginBottom: spacing.sm,
    fontSize: fontSize.lg,
  },
  selectedRow: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    padding: spacing.sm,
    marginBottom: spacing.sm,
    backgroundColor: colors.surface,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  selectedRowActive: {
    borderColor: colors.primary,
    backgroundColor: "#EFF6FF",
  },
  availableRow: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    padding: spacing.sm,
    marginBottom: spacing.sm,
    backgroundColor: colors.surface,
  },
  rowMain: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  branchInfo: {
    marginLeft: spacing.sm,
    flex: 1,
  },
  branchTitle: {
    color: colors.text,
    fontSize: fontSize.md,
    fontWeight: "600",
  },
  seatText: {
    marginTop: spacing.xs,
    fontSize: fontSize.sm,
    fontWeight: "600",
  },
  priorityBadge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },
  priorityBadgeText: {
    color: "#fff",
    fontSize: fontSize.sm,
    fontWeight: "700",
  },
  rowActions: {
    flexDirection: "row",
    alignItems: "center",
    marginLeft: spacing.sm,
  },
  iconButton: {
    padding: spacing.xs,
    marginLeft: spacing.xs,
  },
  errorText: {
    color: colors.danger,
    marginBottom: spacing.sm,
  },
  emptyText: {
    color: colors.textSecondary,
  },
});

export default BranchSelectScreen;
