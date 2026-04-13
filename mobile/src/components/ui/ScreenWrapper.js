import React from "react";
import { SafeAreaView, ScrollView, StyleSheet, View } from "react-native";

import { colors, spacing } from "../../theme";

const ScreenWrapper = ({
  children,
  scroll = true,
  contentStyle,
  safeAreaStyle,
  padded = true,
}) => {
  const Container = scroll ? ScrollView : View;
  return (
    <SafeAreaView style={[styles.safeArea, safeAreaStyle]}>
      <Container
        style={styles.container}
        contentContainerStyle={[
          scroll && styles.scrollContent,
          padded && styles.padded,
          contentStyle,
        ]}
        showsVerticalScrollIndicator={false}
      >
        {children}
      </Container>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  padded: {
    padding: spacing.md,
  },
});

export default ScreenWrapper;
