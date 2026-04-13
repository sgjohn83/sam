import React, { useMemo, useState } from "react";
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { colors, fontSize, spacing } from "../../theme";

const Select = ({
  label,
  placeholder = "Select",
  options = [],
  value,
  onChange,
  error,
  helperText,
  disabled = false,
}) => {
  const [open, setOpen] = useState(false);
  const selected = useMemo(
    () => options.find((item) => item.value === value),
    [options, value]
  );

  return (
    <View style={styles.container}>
      {label ? <Text style={styles.label}>{label}</Text> : null}
      <Pressable
        style={[styles.trigger, disabled && styles.triggerDisabled, error && styles.errorBorder]}
        onPress={() => {
          if (!disabled) {
            setOpen(true);
          }
        }}
      >
        <Text style={[styles.triggerText, !selected && styles.placeholder]}>
          {selected ? selected.label : placeholder}
        </Text>
      </Pressable>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {!error && helperText ? <Text style={styles.helper}>{helperText}</Text> : null}

      <Modal visible={open} transparent animationType="fade" onRequestClose={() => setOpen(false)}>
        <Pressable style={styles.overlay} onPress={() => setOpen(false)}>
          <View style={styles.modalCard}>
            <ScrollView>
              {options.map((item) => (
                <Pressable
                  key={String(item.value)}
                  style={styles.option}
                  onPress={() => {
                    onChange?.(item.value);
                    setOpen(false);
                  }}
                >
                  <Text style={styles.optionText}>{item.label}</Text>
                </Pressable>
              ))}
            </ScrollView>
          </View>
        </Pressable>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { marginBottom: spacing.md },
  label: {
    marginBottom: spacing.xs,
    color: colors.textSecondary,
    fontWeight: "600",
    fontSize: fontSize.md,
  },
  trigger: {
    minHeight: 44,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    borderRadius: 10,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
  triggerDisabled: {
    backgroundColor: colors.disabled,
  },
  triggerText: { color: colors.text, fontSize: fontSize.md },
  placeholder: { color: colors.textSecondary },
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    justifyContent: "center",
    padding: spacing.lg,
  },
  modalCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    maxHeight: "60%",
    paddingVertical: spacing.sm,
  },
  option: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
  },
  optionText: { color: colors.text, fontSize: fontSize.md },
  errorBorder: { borderColor: colors.danger },
  error: { marginTop: spacing.xs, color: colors.danger, fontSize: fontSize.sm },
  helper: { marginTop: spacing.xs, color: colors.textSecondary, fontSize: fontSize.sm },
});

export default Select;
