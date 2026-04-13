import React from "react";
import { SafeAreaView, ScrollView, StyleSheet, View } from "react-native";

import colors from "../../theme/colors";
import spacing from "../../theme/spacing";

const ScreenWrapper = ({ children, scroll = true }) => {
  const Body = scroll ? ScrollView : View;
  return (
    <SafeAreaView style={styles.safe}>
      <Body
        style={styles.body}
        contentContainerStyle={scroll ? styles.content : undefined}
        showsVerticalScrollIndicator={false}
      >
        {children}
      </Body>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  body: { flex: 1 },
  content: { padding: spacing.md, gap: spacing.md },
});

export default ScreenWrapper;
