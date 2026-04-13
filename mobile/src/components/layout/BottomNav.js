import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import colors from "../../theme/colors";
import spacing from "../../theme/spacing";

const BottomNav = ({ items = [], active, onPress }) => (
  <View style={styles.root}>
    {items.map((item) => {
      const isActive = item.key === active;
      return (
        <Pressable key={item.key} style={styles.item} onPress={() => onPress?.(item.key)}>
          <Text style={[styles.label, isActive && styles.active]}>{item.label}</Text>
        </Pressable>
      );
    })}
  </View>
);

const styles = StyleSheet.create({
  root: {
    flexDirection: "row",
    borderTopWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    paddingVertical: spacing.sm,
  },
  item: { flex: 1, alignItems: "center" },
  label: { color: colors.textSecondary, fontWeight: "600" },
  active: { color: colors.primary },
});

export default BottomNav;
