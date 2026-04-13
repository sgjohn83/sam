import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, fontSize } from "../../theme";

const mapColor = {
  success: { bg: "#DCFCE7", text: colors.success },
  warning: { bg: "#FEF3C7", text: colors.warning },
  danger: { bg: "#FEE2E2", text: colors.danger },
  neutral: { bg: "#E5E7EB", text: colors.textSecondary },
};

const Badge = ({ text, tone = "neutral", color }) => {
  const legacyTone =
    color === "green" ? "success" : color === "yellow" ? "warning" : color === "red" ? "danger" : color ? "neutral" : tone;
  const palette = mapColor[legacyTone] || mapColor.neutral;
  return (
    <View style={[styles.badge, { backgroundColor: palette.bg }]}>
      <Text style={[styles.text, { color: palette.text }]}>{text}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: { alignSelf: "flex-start", borderRadius: 999, paddingVertical: 4, paddingHorizontal: 10 },
  text: { fontSize: fontSize.sm, fontWeight: "700" },
});

export default Badge;
