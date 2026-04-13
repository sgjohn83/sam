import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import { colors, fontSize, spacing } from "../theme";

const DOC_LABELS = {
  aadhar: "Aadhar",
  marksheet_10: "SSC",
  marksheet_12: "Inter",
  rank_card: "Rank Card",
};

const CrossVerifyAlert = ({
  namesFound = {},
  mismatches = [],
  dismissed = false,
  onDismiss,
}) => {
  if (dismissed || !Object.keys(namesFound).length) {
    return null;
  }

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>Name Mismatch Detected</Text>
        <Pressable onPress={onDismiss} style={styles.dismissBtn}>
          <Feather name="x" size={18} color="#92400E" />
        </Pressable>
      </View>

      <Text style={styles.subtitle}>Different names found across your documents:</Text>

      <View style={styles.namesWrap}>
        {Object.entries(namesFound).map(([docKey, name]) => {
          const isMismatch = mismatches.includes(docKey);
          return (
            <View key={docKey} style={styles.row}>
              <Text style={styles.docLabel}>{`${DOC_LABELS[docKey] || docKey}:`}</Text>
              <Text style={[styles.nameValue, isMismatch && styles.mismatchValue]}>
                {String(name || "-")}
              </Text>
            </View>
          );
        })}
      </View>

      <Text style={styles.footerText}>
        Please verify the correct spelling in the Name field below.
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#FEF3C7",
    borderColor: colors.warning,
    borderWidth: 1,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: spacing.xs,
  },
  title: {
    color: "#92400E",
    fontSize: fontSize.lg,
    fontWeight: "700",
  },
  dismissBtn: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(146, 64, 14, 0.12)",
  },
  subtitle: {
    color: "#92400E",
    marginBottom: spacing.sm,
  },
  namesWrap: {
    marginBottom: spacing.sm,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.xs,
  },
  docLabel: {
    minWidth: 90,
    color: colors.textSecondary,
    fontWeight: "600",
  },
  nameValue: {
    color: colors.text,
    fontWeight: "700",
  },
  mismatchValue: {
    color: colors.danger,
  },
  footerText: {
    color: "#92400E",
    fontWeight: "600",
  },
});

export default CrossVerifyAlert;
