import React from "react";
import { StyleSheet, Text, View } from "react-native";

import colors from "../../theme/colors";
import spacing from "../../theme/spacing";

const Header = ({ title, subtitle }) => (
  <View style={styles.root}>
    <Text style={styles.title}>{title}</Text>
    {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
  </View>
);

const styles = StyleSheet.create({
  root: { marginBottom: spacing.sm },
  title: { fontSize: 24, fontWeight: "700", color: colors.textPrimary },
  subtitle: { marginTop: 4, color: colors.textSecondary },
});

export default Header;
