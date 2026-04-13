import React from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import { colors } from "../../theme";

const Spinner = ({ size = "small", color = colors.primary, fullScreen = false }) => (
  <View style={fullScreen ? styles.fullScreen : styles.inline}>
    <ActivityIndicator color={color} size={size} />
  </View>
);

const styles = StyleSheet.create({
  inline: { alignItems: "center", justifyContent: "center" },
  fullScreen: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
});

export default Spinner;
