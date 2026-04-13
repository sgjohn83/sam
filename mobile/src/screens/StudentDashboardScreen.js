import React, { useEffect, useMemo, useRef } from "react";
import {
  Animated,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useQuery } from "@tanstack/react-query";
import { Feather } from "@expo/vector-icons";

import ScreenWrapper from "../components/layout/ScreenWrapper";
import Card from "../components/ui/Card";
import Badge from "../components/ui/Badge";
import Spinner from "../components/ui/Spinner";
import { documentApi } from "../services/documentApi";
import { ROUTES } from "../constants/routes";
import useAuth from "../hooks/useAuth";
import studentApi from "../services/studentApi";
import { colors, fontSize, spacing } from "../theme";

const STEP_KEYS = [
  { key: "register", label: "Register" },
  { key: "profile", label: "Profile" },
  { key: "documents", label: "Documents" },
  { key: "submit", label: "Submit" },
  { key: "verify", label: "Verify" },
  { key: "seat", label: "Seat" },
  { key: "fee", label: "Fee" },
  { key: "admitted", label: "Admitted" },
];

const getStepStates = (rawData) => {
  const rawSteps = rawData?.progress?.steps || rawData?.steps || {};
  const currentStepRaw = rawData?.progress?.current_step || rawData?.current_step || "";
  const currentStep = String(currentStepRaw).toLowerCase();
  const currentIndexFromStep = STEP_KEYS.findIndex((step) => step.key === currentStep);
  const completedCountFromResponse =
    Number(rawData?.progress?.completed_count) || Number(rawData?.completed_steps_count) || 0;

  return STEP_KEYS.map((step, index) => {
    const responseState = String(rawSteps[step.key] || "").toLowerCase();
    if (responseState === "completed") {
      return "completed";
    }
    if (responseState === "current" || responseState === "in_progress") {
      return "current";
    }
    if (responseState === "future" || responseState === "pending") {
      return "future";
    }
    if (currentIndexFromStep >= 0) {
      if (index < currentIndexFromStep) {
        return "completed";
      }
      if (index === currentIndexFromStep) {
        return "current";
      }
      return "future";
    }
    if (completedCountFromResponse > 0) {
      if (index < completedCountFromResponse) {
        return "completed";
      }
      if (index === completedCountFromResponse) {
        return "current";
      }
    }
    return "future";
  });
};

const mapApplicationTone = (status) => {
  const value = String(status || "").toLowerCase();
  if (["verified", "approved", "submitted", "admitted"].includes(value)) {
    return "success";
  }
  if (["draft", "processing", "pending"].includes(value)) {
    return "warning";
  }
  if (["rejected", "error", "failed"].includes(value)) {
    return "danger";
  }
  return "neutral";
};

const REQUIRED_DOCS = [
  { key: "aadhar", label: "Aadhar Card" },
  { key: "marksheet_10", label: "10th Marksheet" },
  { key: "marksheet_12", label: "12th Marksheet" },
  { key: "rank_card", label: "Rank Card" },
];

const DOC_ALIASES = {
  aadhar: "aadhar",
  aadhaar: "aadhar",
  marksheet_10: "marksheet_10",
  ssc: "marksheet_10",
  marksheet_12: "marksheet_12",
  inter: "marksheet_12",
  rank_card: "rank_card",
  rank: "rank_card",
};

const normalizeDocStatus = (value) => {
  const status = String(value || "").toLowerCase();
  if (status === "extracted") {
    return "extracted";
  }
  if (status === "verified") {
    return "verified";
  }
  if (status === "rejected") {
    return "rejected";
  }
  if (status === "processing" || status === "uploaded") {
    return "processing";
  }
  return "not_uploaded";
};

const StudentDashboardScreen = ({ navigation }) => {
  const { user } = useAuth();
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.18,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
      ])
    );
    animation.start();
    return () => animation.stop();
  }, [pulseAnim]);

  const query = useQuery({
    queryKey: ["student-profile-completion"],
    queryFn: async () => {
      const { data } = await studentApi.getProfileCompletion();
      return data || {};
    },
  });
  const documentsQuery = useQuery({
    queryKey: ["dashboard-documents"],
    queryFn: async () => {
      const { data } = await documentApi.getDocuments();
      return data || [];
    },
  });

  const profileData = query.data || {};
  const stepStates = useMemo(() => getStepStates(profileData), [profileData]);
  const completedSteps = stepStates.filter((state) => state === "completed").length;

  const fullName =
    profileData?.student_name ||
    profileData?.profile?.full_name ||
    user?.full_name ||
    "Student";
  const applicationNo =
    profileData?.application_number || profileData?.application_id || "ADM-2026-00001";

  const profileMessage =
    profileData?.profile?.message ||
    (Number.isFinite(profileData?.profile?.missing_fields_count)
      ? profileData.profile.missing_fields_count > 0
        ? `${profileData.profile.missing_fields_count} fields missing`
        : "Profile complete"
      : "Profile complete");

  const rawDocuments = documentsQuery.data || [];
  const docsByType = {};
  rawDocuments.forEach((doc) => {
    const canonical = DOC_ALIASES[String(doc.document_type || "").toLowerCase()];
    if (!canonical) {
      return;
    }
    docsByType[canonical] = doc;
  });
  const dashboardDocs = REQUIRED_DOCS.map((required) => {
    const doc = docsByType[required.key];
    const status = normalizeDocStatus(doc?.status);
    const confidence =
      doc?.ocr_result?.overall_confidence ??
      doc?.latest_ocr_result?.overall_confidence ??
      null;
    return {
      key: required.key,
      label: required.label,
      status,
      confidence,
    };
  });
  const docsUploaded = dashboardDocs.filter((doc) => doc.status !== "not_uploaded").length;
  const docsRequired = REQUIRED_DOCS.length;

  const appStatus =
    profileData?.application?.status || profileData?.application_status || "draft";
  const appNext =
    profileData?.application?.next_step ||
    profileData?.application?.next_step_description ||
    "Continue your application";

  const unreadCount = Number(profileData?.notifications?.unread_count ?? 0);

  if (query.isLoading || documentsQuery.isLoading) {
    return <Spinner fullScreen size="large" />;
  }

  return (
    <ScreenWrapper scroll={false} padded={false}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={query.isRefetching || documentsQuery.isRefetching}
            onRefresh={() => {
              query.refetch();
              documentsQuery.refetch();
            }}
          />
        }
      >
        <View style={styles.header}>
          <Text style={styles.welcome}>Welcome, {fullName}</Text>
          <Text style={styles.applicationId}>{applicationNo}</Text>
        </View>

        <Card style={styles.stepperCard}>
          <View style={styles.stepperHead}>
            <Text style={styles.stepperTitle}>Admission Progress</Text>
            <Text style={styles.stepperCount}>{completedSteps}/{STEP_KEYS.length}</Text>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.stepperRow}>
              {STEP_KEYS.map((step, index) => {
                const state = stepStates[index];
                return (
                  <View key={step.key} style={styles.stepItem}>
                    <View style={styles.circleContainer}>
                      {state === "current" ? (
                        <Animated.View
                          style={[
                            styles.pulseRing,
                            {
                              transform: [{ scale: pulseAnim }],
                              opacity: pulseAnim.interpolate({
                                inputRange: [1, 1.18],
                                outputRange: [0.4, 0.15],
                              }),
                            },
                          ]}
                        />
                      ) : null}
                      <View
                        style={[
                          styles.circle,
                          state === "completed" && styles.completedCircle,
                          state === "current" && styles.currentCircle,
                          state === "future" && styles.futureCircle,
                        ]}
                      >
                        <Text style={styles.circleText}>
                          {state === "completed" ? "✓" : ""}
                        </Text>
                      </View>
                    </View>
                    <Text style={styles.stepLabel}>{step.label}</Text>
                  </View>
                );
              })}
            </View>
          </ScrollView>
        </Card>

        <Pressable onPress={() => navigation.navigate(ROUTES.PROFILE.EDIT)}>
          <Card style={styles.actionCard}>
            <Text style={styles.cardTitle}>Profile</Text>
            <Text style={styles.cardText}>{profileMessage}</Text>
          </Card>
        </Pressable>

        <Pressable onPress={() => navigation.navigate("DocumentsTab")}>
          <Card style={styles.actionCard}>
            <View style={styles.docHeaderRow}>
              <View style={styles.docTitleRow}>
                <Text style={styles.docIcon}>{"\uD83D\uDCC4"}</Text>
                <Text style={styles.cardTitle}>Documents</Text>
              </View>
              <Text style={styles.docCount}>{`${docsUploaded}/${docsRequired}`}</Text>
            </View>
            <View style={styles.miniStatusWrap}>
              {dashboardDocs.map((doc) => (
                <View key={doc.key} style={styles.docRow}>
                  <Text style={styles.docLabel}>{doc.label}</Text>
                  {doc.status === "extracted" && typeof doc.confidence === "number" ? (
                    <View style={styles.confBadge}>
                      <Text style={styles.confBadgeText}>{`${Math.round(doc.confidence * 100)}%`}</Text>
                    </View>
                  ) : doc.status === "verified" ? (
                    <Text style={styles.docConfidence}>Verified</Text>
                  ) : doc.status === "processing" ? (
                    <View style={styles.processingRow}>
                      <Feather name="loader" size={12} color={colors.primary} />
                      <Text style={styles.docProcessing}>Processing</Text>
                    </View>
                  ) : (
                    <Text style={styles.docMissing}>Not uploaded</Text>
                  )}
                </View>
              ))}
            </View>
            {docsUploaded < docsRequired ? (
              <View style={styles.uploadPromptWrap}>
                <Text style={styles.uploadPrompt}>Upload Remaining Documents</Text>
              </View>
            ) : null}
          </Card>
        </Pressable>

        <Pressable onPress={() => navigation.navigate("ApplicationTab")}>
          <Card style={styles.actionCard}>
            <Text style={styles.cardTitle}>Application</Text>
            <Badge text={String(appStatus).toUpperCase()} tone={mapApplicationTone(appStatus)} />
            <Text style={[styles.cardText, styles.cardTextTop]}>{appNext}</Text>
          </Card>
        </Pressable>

        <Pressable onPress={() => navigation.navigate(ROUTES.NOTIFICATIONS.LIST)}>
          <Card style={styles.actionCard}>
            <Text style={styles.cardTitle}>Notifications</Text>
            <Text style={styles.cardText}>
              {unreadCount > 0 ? `${unreadCount} unread notifications` : "No unread notifications"}
            </Text>
          </Card>
        </Pressable>
      </ScrollView>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  header: {
    marginBottom: spacing.md,
  },
  welcome: {
    color: colors.text,
    fontSize: fontSize.xl,
    fontWeight: "700",
  },
  applicationId: {
    color: colors.textSecondary,
    fontSize: fontSize.md,
    marginTop: spacing.xs,
  },
  stepperCard: {
    marginBottom: spacing.md,
  },
  stepperHead: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: spacing.md,
  },
  stepperTitle: {
    fontSize: fontSize.lg,
    color: colors.text,
    fontWeight: "700",
  },
  stepperCount: {
    color: colors.textSecondary,
    fontWeight: "600",
  },
  stepperRow: {
    flexDirection: "row",
    alignItems: "flex-start",
  },
  stepItem: {
    width: 84,
    alignItems: "center",
    marginRight: spacing.sm,
  },
  circleContainer: {
    width: 28,
    height: 28,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.xs,
  },
  pulseRing: {
    position: "absolute",
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.primaryLight,
  },
  circle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  completedCircle: {
    backgroundColor: colors.success,
    borderColor: colors.success,
  },
  currentCircle: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  futureCircle: {
    backgroundColor: colors.disabled,
    borderColor: colors.disabled,
  },
  circleText: {
    color: "#fff",
    fontSize: fontSize.sm,
    fontWeight: "700",
    lineHeight: 14,
  },
  stepLabel: {
    color: colors.textSecondary,
    fontSize: fontSize.sm,
    textAlign: "center",
  },
  actionCard: {
    marginBottom: spacing.md,
  },
  cardTitle: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: "700",
    marginBottom: spacing.xs,
  },
  cardText: {
    color: colors.textSecondary,
    fontSize: fontSize.md,
  },
  cardTextTop: {
    marginTop: spacing.sm,
  },
  miniStatusWrap: {
    marginTop: spacing.sm,
  },
  docHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  docTitleRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  docIcon: {
    marginRight: spacing.xs,
    fontSize: fontSize.md,
  },
  docCount: {
    color: colors.textSecondary,
    fontWeight: "700",
  },
  docRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: spacing.xs,
  },
  docLabel: {
    color: colors.text,
    fontSize: fontSize.sm,
    flex: 1,
    marginRight: spacing.md,
  },
  docConfidence: {
    color: colors.success,
    fontSize: fontSize.sm,
    fontWeight: "700",
  },
  confBadge: {
    backgroundColor: "#DCFCE7",
    borderRadius: 999,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
  },
  confBadgeText: {
    color: colors.success,
    fontSize: fontSize.sm,
    fontWeight: "700",
  },
  docMissing: {
    color: colors.textSecondary,
    fontSize: fontSize.sm,
  },
  processingRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  docProcessing: {
    marginLeft: 4,
    color: colors.primary,
    fontSize: fontSize.sm,
  },
  uploadPromptWrap: {
    marginTop: spacing.sm,
    paddingVertical: spacing.xs,
  },
  uploadPrompt: {
    color: colors.primary,
    fontWeight: "700",
    fontSize: fontSize.sm,
  },
});

export default StudentDashboardScreen;
