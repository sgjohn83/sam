import React, { useMemo } from "react";
import { ActivityIndicator, Modal, Pressable, StyleSheet, Text, View } from "react-native";

import { colors, fontSize, spacing } from "../../theme";

const TIMEOUT_MS = 120000;
const ALMOST_DONE_MS = 20000;

const UploadOverlay = ({
  visible = false,
  phase = "upload",
  progress = null,
  elapsedMs = 0,
  onCancel,
}) => {
  const state = useMemo(() => {
    if (elapsedMs >= TIMEOUT_MS) {
      return {
        title: "Taking longer than expected",
        subtitle: "You can keep waiting or cancel and try again.",
        step: "Still processing...",
        timedOut: true,
      };
    }

    if (phase === "upload") {
      return {
        title: "Uploading document...",
        subtitle: "This may take up to 30 seconds",
        step: "Step 1/3: Uploading file...",
        timedOut: false,
      };
    }

    if (elapsedMs >= ALMOST_DONE_MS) {
      return {
        title: "Almost done...",
        subtitle: "Finalizing extracted details",
        step: "Step 3/3: Finalizing...",
        timedOut: false,
      };
    }

    return {
      title: "Processing with AI...",
      subtitle: "This may take up to 30 seconds",
      step: "Step 2/3: Extracting data...",
      timedOut: false,
    };
  }, [elapsedMs, phase]);

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={() => {}}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.title}>{state.title}</Text>
          <Text style={styles.subtitle}>{state.subtitle}</Text>
          {typeof progress === "number" ? (
            <Text style={styles.progress}>{Math.max(0, Math.min(100, Math.round(progress)))}%</Text>
          ) : null}
          <Text style={styles.step}>{state.step}</Text>

          {state.timedOut ? (
            <Pressable style={styles.cancelButton} onPress={onCancel}>
              <Text style={styles.cancelText}>Cancel</Text>
            </Pressable>
          ) : null}
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.lg,
  },
  card: {
    width: "100%",
    maxWidth: 360,
    backgroundColor: colors.surface,
    borderRadius: 12,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xl,
    alignItems: "center",
  },
  title: {
    marginTop: spacing.md,
    color: colors.text,
    fontSize: fontSize.xl,
    fontWeight: "700",
    textAlign: "center",
  },
  subtitle: {
    marginTop: spacing.sm,
    color: colors.textSecondary,
    fontSize: fontSize.md,
    textAlign: "center",
  },
  progress: {
    marginTop: spacing.md,
    color: colors.primary,
    fontSize: fontSize.xxl,
    fontWeight: "700",
  },
  step: {
    marginTop: spacing.sm,
    color: colors.textSecondary,
    fontSize: fontSize.md,
    textAlign: "center",
  },
  cancelButton: {
    marginTop: spacing.lg,
    backgroundColor: colors.danger,
    borderRadius: 8,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  cancelText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: fontSize.md,
  },
});

export default UploadOverlay;
