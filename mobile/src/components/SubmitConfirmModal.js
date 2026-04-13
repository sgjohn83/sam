import React from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import Button from "./ui/Button";
import Spinner from "./ui/Spinner";
import { colors, fontSize, spacing } from "../theme";

const SubmitConfirmModal = ({
  visible,
  onCancel,
  onConfirm,
  submitting = false,
  applicationNumber = "",
  branchPreferences = [],
}) => {
  return (
    <Modal transparent visible={visible} animationType="fade" onRequestClose={onCancel}>
      <View style={styles.overlay}>
        {submitting ? (
          <View style={styles.loadingCard}>
            <Spinner size="large" />
            <Text style={styles.loadingTitle}>Submitting application...</Text>
            <Text style={styles.loadingSubtitle}>Please wait</Text>
          </View>
        ) : (
          <View style={styles.card}>
            <View style={styles.titleRow}>
              <Feather name="alert-circle" size={18} color={colors.warning} />
              <Text style={styles.title}>Submit Application?</Text>
            </View>

            <Text style={styles.message}>
              Once submitted, you cannot edit your profile or change documents.
            </Text>

            <Text style={styles.metaLabel}>Application: {applicationNumber || "-"}</Text>

            <Text style={styles.metaLabel}>Branch Preferences:</Text>
            <View style={styles.branchList}>
              {branchPreferences.length > 0 ? (
                branchPreferences.map((branch, index) => (
                  <Text key={String(branch?.id || `${index}`)} style={styles.branchItem}>
                    {index + 1}. {branch?.code || ""} {branch?.name ? `- ${branch.name}` : ""}
                  </Text>
                ))
              ) : (
                <Text style={styles.branchItem}>No branch preferences selected</Text>
              )}
            </View>

            <View style={styles.actionRow}>
              <Pressable style={[styles.actionBtn, styles.cancelBtn]} onPress={onCancel}>
                <Text style={styles.cancelText}>Cancel</Text>
              </Pressable>
              <View style={styles.confirmWrap}>
                <Button title="Confirm Submit" onPress={onConfirm} />
              </View>
            </View>
          </View>
        )}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(17, 24, 39, 0.55)",
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.md,
  },
  card: {
    width: "100%",
    maxWidth: 420,
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.sm,
  },
  title: {
    marginLeft: spacing.xs,
    fontSize: fontSize.xl,
    fontWeight: "700",
    color: colors.text,
  },
  message: {
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  metaLabel: {
    color: colors.text,
    fontWeight: "600",
    marginBottom: spacing.xs,
  },
  branchList: {
    marginBottom: spacing.md,
  },
  branchItem: {
    color: colors.text,
    marginBottom: spacing.xs,
  },
  actionRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  actionBtn: {
    flex: 1,
    minHeight: 44,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  cancelBtn: {
    borderColor: colors.border,
    backgroundColor: colors.surface,
    marginRight: spacing.sm,
  },
  cancelText: {
    color: colors.text,
    fontWeight: "600",
  },
  confirmWrap: {
    flex: 1.4,
  },
  loadingCard: {
    width: "100%",
    maxWidth: 320,
    backgroundColor: colors.surface,
    borderRadius: 14,
    paddingVertical: spacing.xl,
    paddingHorizontal: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  loadingTitle: {
    marginTop: spacing.md,
    color: colors.text,
    fontWeight: "700",
    fontSize: fontSize.lg,
  },
  loadingSubtitle: {
    marginTop: spacing.xs,
    color: colors.textSecondary,
  },
});

export default SubmitConfirmModal;
