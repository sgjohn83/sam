import React, { useEffect, useMemo, useRef, useState } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";
import { Feather } from "@expo/vector-icons";
import { useMutation, useQuery } from "@tanstack/react-query";
import Toast from "react-native-toast-message";

import Header from "../../components/layout/Header";
import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import studentApi from "../../services/studentApi";
import { pickFromCamera, pickFromGallery } from "../../utils/filePicker";
import { ROUTES } from "../../constants/routes";
import { colors, fontSize, spacing } from "../../theme";

const DEFAULT_TIMELINE = [
  { key: "register", label: "Register", state: "completed", date: "Apr 10, 2026" },
  { key: "profile_created", label: "Profile Created", state: "completed", date: "Apr 10, 2026" },
  { key: "documents_uploaded", label: "Documents Uploaded", state: "completed", date: "Apr 11, 2026" },
  {
    key: "application_submitted",
    label: "Application Submitted",
    state: "completed",
    date: "Apr 12, 2026",
  },
  { key: "under_verification", label: "Under Verification", state: "current", date: "In Progress" },
  { key: "verified", label: "Verified", state: "future", date: "Pending" },
  { key: "seat_allocated", label: "Seat Allocated", state: "future", date: "Pending" },
  { key: "fee_payment", label: "Fee Payment", state: "future", date: "Pending" },
  { key: "admitted", label: "Admitted", state: "future", date: "Pending" },
];

const normalizeTimeline = (data) => {
  const timeline = data?.timeline;
  if (Array.isArray(timeline) && timeline.length) {
    return timeline.map((item) => ({
      key: item.key || item.id || item.label,
      label: item.label,
      state: item.state || "future",
      date: item.date || (item.state === "current" ? "In Progress" : "Pending"),
    }));
  }
  return DEFAULT_TIMELINE;
};

const StatusScreen = ({ navigation }) => {
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const [selectedProofFile, setSelectedProofFile] = useState(null);

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
    queryKey: ["student-application-status"],
    queryFn: async () => {
      const { data } = await studentApi.getStatus();
      return data || {};
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file) => studentApi.uploadPaymentProof(file),
    onSuccess: () => {
      Toast.show({
        type: "success",
        text1: "Payment proof uploaded. Awaiting confirmation.",
      });
      setSelectedProofFile(null);
      query.refetch();
    },
    onError: (error) => {
      const message =
        error?.response?.data?.error ||
        error?.response?.data?.detail ||
        "Failed to upload payment proof";
      Toast.show({
        type: "error",
        text1: message,
      });
    },
  });

  const timelineItems = useMemo(() => normalizeTimeline(query.data), [query.data]);
  const rejection = query.data?.rejected_document || null;
  const isSeatAllocated =
    Boolean(query.data?.seat_allocated) ||
    timelineItems.some((item) => item.key === "seat_allocated" && item.state === "completed");
  const seatDetails = query.data?.seat_details || {
    branch: "Computer Science & Engineering (CSE)",
    quota: "OBC",
    fee_amount: "₹1,20,000",
    deadline: "May 15, 2026",
  };

  const applicationStatus = String(query.data?.application_status || "").toLowerCase();
  const isFeePending = applicationStatus === "fee_pending";

  const feeDetails = query.data?.fee_details || {};
  const branchLabel = feeDetails.branch || seatDetails.branch || "CSE";
  const totalFee = feeDetails.total_fee || seatDetails.fee_amount || "₹1,20,000";
  const concession = feeDetails.concession || "₹0";
  const amountDue = feeDetails.amount_due || totalFee;
  const paymentMode = feeDetails.payment_mode || "Bank Transfer / DD";
  const accountMasked = feeDetails.account || "XXXXXXX (shown by college)";
  const paymentDeadline = feeDetails.deadline || seatDetails.deadline || "May 15, 2026";

  const onPickCamera = async () => {
    try {
      const file = await pickFromCamera();
      if (file) {
        setSelectedProofFile(file);
      }
    } catch (error) {
      Toast.show({
        type: "error",
        text1: error?.message || "Unable to capture image",
      });
    }
  };

  const onPickGallery = async () => {
    try {
      const file = await pickFromGallery();
      if (file) {
        setSelectedProofFile(file);
      }
    } catch (error) {
      Toast.show({
        type: "error",
        text1: error?.message || "Unable to pick image",
      });
    }
  };

  if (query.isLoading) {
    return <Spinner fullScreen size="large" />;
  }

  return (
    <ScreenWrapper>
      <Header title="Application Status" subtitle="Track progress in real time" />

      <Card style={styles.timelineCard}>
        {timelineItems.map((item, index) => {
          const isCompleted = item.state === "completed";
          const isCurrent = item.state === "current";
          const isFuture = !isCompleted && !isCurrent;
          const isLast = index === timelineItems.length - 1;

          return (
            <View key={String(item.key || index)} style={styles.timelineRow}>
              <View style={styles.markerCol}>
                <View style={styles.markerContainer}>
                  {isCurrent ? (
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
                      styles.marker,
                      isCompleted && styles.completedMarker,
                      isCurrent && styles.currentMarker,
                      isFuture && styles.futureMarker,
                    ]}
                  >
                    <Text style={styles.markerText}>{isCompleted ? "✓" : ""}</Text>
                  </View>
                </View>
                {!isLast ? <View style={styles.connector} /> : null}
              </View>
              <View style={styles.contentCol}>
                <Text style={styles.stepTitle}>{item.label}</Text>
                <Text style={[styles.stepMeta, isCurrent && styles.inProgress]}>
                  {isCurrent ? "In Progress" : item.date || "Pending"}
                </Text>
              </View>
            </View>
          );
        })}
      </Card>

      {rejection ? (
        <Card style={styles.alertCard}>
          <Text style={styles.alertTitle}>Action Required</Text>
          <Text style={styles.alertText}>
            Your {rejection.document_name || "document"} was rejected: "
            {rejection.reason || "Please re-upload"}"
          </Text>
          <Button title="Re-upload Now" onPress={() => navigation.navigate("DocumentsTab")} />
        </Card>
      ) : null}

      {isSeatAllocated ? (
        <Card style={styles.seatCard}>
          <Text style={styles.seatTitle}>Seat Details</Text>
          <Text style={styles.seatText}>Branch: {seatDetails.branch}</Text>
          <Text style={styles.seatText}>Quota: {seatDetails.quota}</Text>
          <Text style={styles.seatText}>Fee Amount: {seatDetails.fee_amount}</Text>
          <Text style={styles.seatText}>Deadline: {seatDetails.deadline}</Text>
          <Button
            title="Upload Payment Proof"
            variant="secondary"
            onPress={() => navigation.navigate(ROUTES.STATUS.SEAT_DETAILS)}
          />
        </Card>
      ) : null}

      {isFeePending ? (
        <Card style={styles.paymentCard}>
          <Text style={styles.paymentTitle}>Fee Payment Details</Text>
          <Text style={styles.paymentText}>Branch: {branchLabel}</Text>
          <Text style={styles.paymentText}>Total Fee: {totalFee}</Text>
          <Text style={styles.paymentText}>Concession: {concession}</Text>
          <Text style={styles.paymentText}>Amount Due: {amountDue}</Text>

          <View style={styles.paymentDivider} />
          <Text style={styles.paymentText}>Payment Mode: {paymentMode}</Text>
          <Text style={styles.paymentText}>Account: {accountMasked}</Text>
          <Text style={styles.paymentText}>Deadline: {paymentDeadline}</Text>

          <Text style={styles.uploadHint}>Upload payment receipt/screenshot:</Text>
          <View style={styles.pickerRow}>
            <Button title="Capture" variant="secondary" onPress={onPickCamera} />
            <Button title="Gallery" variant="secondary" onPress={onPickGallery} />
          </View>

          {selectedProofFile ? (
            <View style={styles.fileRow}>
              <Feather name="paperclip" size={14} color={colors.primary} />
              <Text style={styles.fileText} numberOfLines={1}>
                {selectedProofFile.fileName || "Selected image"}
              </Text>
            </View>
          ) : null}

          <Button
            title="Upload Payment Proof"
            onPress={() => uploadMutation.mutate(selectedProofFile)}
            loading={uploadMutation.isPending}
            disabled={!selectedProofFile}
          />
        </Card>
      ) : null}
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  timelineCard: {
    marginBottom: spacing.md,
  },
  timelineRow: {
    flexDirection: "row",
  },
  markerCol: {
    width: 30,
    alignItems: "center",
  },
  markerContainer: {
    width: 24,
    height: 24,
    alignItems: "center",
    justifyContent: "center",
  },
  pulseRing: {
    position: "absolute",
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.primaryLight,
  },
  marker: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  completedMarker: {
    backgroundColor: colors.success,
    borderColor: colors.success,
  },
  currentMarker: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  futureMarker: {
    backgroundColor: colors.surface,
    borderColor: colors.disabled,
  },
  markerText: {
    color: "#fff",
    fontSize: fontSize.sm,
    fontWeight: "700",
    lineHeight: 12,
  },
  connector: {
    width: 2,
    flex: 1,
    backgroundColor: colors.border,
    marginVertical: 4,
  },
  contentCol: {
    flex: 1,
    paddingBottom: spacing.md,
  },
  stepTitle: {
    fontSize: fontSize.md,
    color: colors.text,
    fontWeight: "600",
  },
  stepMeta: {
    marginTop: 2,
    color: colors.textSecondary,
    fontSize: fontSize.sm,
  },
  inProgress: {
    color: colors.primary,
    fontWeight: "600",
  },
  alertCard: {
    borderColor: colors.warning,
    backgroundColor: "#FFFBEB",
    marginBottom: spacing.md,
  },
  alertTitle: {
    color: colors.warning,
    fontSize: fontSize.lg,
    fontWeight: "700",
    marginBottom: spacing.xs,
  },
  alertText: {
    color: colors.text,
    marginBottom: spacing.md,
  },
  seatCard: {
    marginBottom: spacing.md,
  },
  seatTitle: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: "700",
    marginBottom: spacing.sm,
  },
  seatText: {
    color: colors.textSecondary,
    marginBottom: spacing.xs,
    fontSize: fontSize.md,
  },
  paymentCard: {
    marginBottom: spacing.md,
  },
  paymentTitle: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: "700",
    marginBottom: spacing.sm,
  },
  paymentText: {
    color: colors.textSecondary,
    marginBottom: spacing.xs,
    fontSize: fontSize.md,
  },
  paymentDivider: {
    height: 1,
    backgroundColor: colors.border,
    marginVertical: spacing.sm,
  },
  uploadHint: {
    marginTop: spacing.sm,
    color: colors.text,
    fontWeight: "600",
    marginBottom: spacing.sm,
  },
  pickerRow: {
    flexDirection: "row",
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  fileRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.sm,
  },
  fileText: {
    marginLeft: spacing.xs,
    color: colors.primary,
    flex: 1,
  },
});

export default StatusScreen;
