import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Button from "../../components/ui/Button";
import { ROUTES } from "../../constants/routes";
import { colors, fontSize, spacing } from "../../theme";

const SubmissionSuccessScreen = ({ navigation, route }) => {
  const applicationNumber = route?.params?.applicationNumber || "";

  return (
    <ScreenWrapper scroll={false}>
      <View style={styles.container}>
        <View style={styles.iconWrap}>
          <Feather name="check-circle" size={64} color={colors.success} />
        </View>
        <Text style={styles.title}>Application Submitted</Text>
        <Text style={styles.subtitle}>
          {applicationNumber
            ? `Your application ${applicationNumber} was submitted successfully.`
            : "Your application was submitted successfully."}
        </Text>

        <View style={styles.actions}>
          <Button
            title="View Status"
            onPress={() =>
              navigation.navigate("StatusTab", {
                screen: ROUTES.STATUS.STATUS,
              })
            }
          />
        </View>
      </View>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
  },
  iconWrap: {
    marginBottom: spacing.lg,
  },
  title: {
    color: colors.text,
    fontWeight: "700",
    fontSize: fontSize.xxl,
    marginBottom: spacing.sm,
    textAlign: "center",
  },
  subtitle: {
    color: colors.textSecondary,
    textAlign: "center",
    marginBottom: spacing.xl,
  },
  actions: {
    width: "100%",
    maxWidth: 320,
  },
});

export default SubmissionSuccessScreen;
