import React from "react";
import { Pressable, StyleSheet, Text } from "react-native";

import { colors, spacing, fontSize } from "../../theme";
import Spinner from "./Spinner";

const Button = ({
  title,
  onPress,
  variant = "primary",
  disabled = false,
  loading = false,
}) => (
  <Pressable
    onPress={onPress}
    disabled={disabled || loading}
    style={[
      styles.base,
      styles[variant] || styles.primary,
      (disabled || loading) && styles.disabled,
    ]}
  >
    {loading ? <Spinner size="small" color={variant === "ghost" ? colors.text : "#fff"} /> : null}
    {!loading ? <Text style={[styles.text, styles[`${variant}Text`]]}>{title}</Text> : null}
  </Pressable>
);

const styles = StyleSheet.create({
  base: {
    borderRadius: 10,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 44,
  },
  primary: {
    backgroundColor: colors.primary,
  },
  secondary: {
    backgroundColor: colors.primaryLight,
  },
  danger: {
    backgroundColor: colors.danger,
  },
  ghost: {
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: colors.border,
  },
  primaryText: { color: "#fff" },
  secondaryText: { color: "#fff" },
  dangerText: { color: "#fff" },
  ghostText: { color: colors.text },
  disabled: {
    opacity: 0.5,
  },
  text: {
    fontSize: fontSize.md,
    fontWeight: "600",
  },
});

export default Button;
