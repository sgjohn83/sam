import React, { useMemo } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useQuery } from "@tanstack/react-query";
import { useFocusEffect } from "@react-navigation/native";
import { Feather } from "@expo/vector-icons";

import Header from "../../components/layout/Header";
import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { documentApi } from "../../services/documentApi";
import studentApi from "../../services/studentApi";
import { ROUTES } from "../../constants/routes";
import { colors, fontSize, spacing } from "../../theme";

const REQUIRED_DOCUMENTS = [
  { key: "aadhar", title: "Aadhar Card" },
  { key: "marksheet_10", title: "10th Marksheet (SSC)" },
  { key: "marksheet_12", title: "12th Marksheet (Inter)" },
  { key: "rank_card", title: "Entrance Rank Card" },
];

const DOC_TYPE_ALIASES = {
  aadhar: "aadhar",
  aadhaar: "aadhar",
  marksheet_10: "marksheet_10",
  ssc: "marksheet_10",
  ssc_marksheet: "marksheet_10",
  marksheet_12: "marksheet_12",
  inter: "marksheet_12",
  inter_marksheet: "marksheet_12",
  rank_card: "rank_card",
  rank: "rank_card",
};

const STATUS_META = {
  not_uploaded: { icon: "circle", color: colors.textSecondary, button: "Upload Now" },
  processing: { icon: "loader", color: colors.primary, button: "Processing..." },
  extracted: { icon: "check-circle", color: colors.success, button: "View Details" },
  verified: { icon: "lock", color: colors.success, button: "View Details" },
  rejected: { icon: "x-circle", color: colors.danger, button: "Re-upload" },
};

const formatDate = (value) => {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

const normalizeStatus = (value) => {
  const normalized = String(value || "").toLowerCase();
  if (["uploaded", "processing"].includes(normalized)) {
    return "processing";
  }
  if (["extracted"].includes(normalized)) {
    return "extracted";
  }
  if (["verified"].includes(normalized)) {
    return "verified";
  }
  if (["rejected"].includes(normalized)) {
    return "rejected";
  }
  return "not_uploaded";
};

const mapDocuments = (documents) => {
  const byType = {};
  (documents || []).forEach((item) => {
    const canonical = DOC_TYPE_ALIASES[String(item.document_type || "").toLowerCase()];
    if (!canonical) {
      return;
    }
    byType[canonical] = item;
  });

  return REQUIRED_DOCUMENTS.map((required) => {
    const record = byType[required.key];
    const status = normalizeStatus(record?.status);
    const ocrResult = record?.ocr_result || record?.latest_ocr_result || null;
    const overallConfidence = ocrResult?.overall_confidence;
    const confidencePercent =
      typeof overallConfidence === "number" ? Math.round(overallConfidence * 100) : null;

    return {
      key: required.key,
      title: required.title,
      id: record?.id || null,
      status,
      confidencePercent,
      uploadedAt: formatDate(record?.uploaded_at || record?.created_at),
      rejectionReason: record?.rejection_reason || null,
    };
  });
};

const getSummaryType = (cards) => {
  const hasRejected = cards.some((card) => card.status === "rejected");
  const uploadedCount = cards.filter((card) => card.status !== "not_uploaded").length;
  const hasMissing = uploadedCount < cards.length;
  if (hasRejected) {
    return "rejected";
  }
  if (!hasMissing) {
    return "complete";
  }
  return "missing";
};

const DocumentCard = ({ item, onAction, highlightRejected, isSubmitted }) => {
  const meta = STATUS_META[item.status];
  const statusLabel = item.status.replace("_", " ");
  const shouldHighlight = highlightRejected && item.status === "rejected";
  const hideUploadAction = isSubmitted && item.status === "not_uploaded";
  const buttonTitle = hideUploadAction ? "Locked" : meta.button;

  return (
    <Card style={[styles.card, shouldHighlight && styles.highlightRejectedCard]}>
      <View style={styles.cardHeader}>
        <Text style={styles.docTitle}>{item.title}</Text>
      </View>

      {item.status === "not_uploaded" ? (
        <View style={styles.statusRow}>
          <Feather name={meta.icon} size={16} color={meta.color} />
          <Text style={[styles.statusText, { color: meta.color }]}>Not uploaded yet</Text>
        </View>
      ) : (
        <>
          <View style={styles.statusRow}>
            {item.status === "processing" ? (
              <ActivityIndicator size="small" color={meta.color} />
            ) : (
              <Feather name={meta.icon} size={16} color={meta.color} />
            )}
            <Text style={[styles.statusText, { color: meta.color }]}>
              Status: {statusLabel.charAt(0).toUpperCase() + statusLabel.slice(1)}
            </Text>
            {item.confidencePercent !== null && item.status !== "rejected" ? (
              <Text style={styles.confidence}>| Confidence: {item.confidencePercent}%</Text>
            ) : null}
          </View>

          {item.uploadedAt ? (
            <Text style={styles.metaText}>Uploaded: {item.uploadedAt}</Text>
          ) : null}

          {item.status === "rejected" && item.rejectionReason ? (
            <Text style={styles.rejection}>Reason: "{item.rejectionReason}"</Text>
          ) : null}
        </>
      )}

      <View style={styles.actionWrap}>
        {hideUploadAction ? (
          <Text style={styles.lockHint}>Upload locked after submission</Text>
        ) : (
          <Button
            title={buttonTitle}
            onPress={onAction}
            variant={item.status === "rejected" ? "danger" : "secondary"}
            disabled={item.status === "processing"}
          />
        )}
      </View>
    </Card>
  );
};

const DocumentListScreen = ({ navigation, route }) => {
  const highlightRejected = Boolean(route?.params?.highlightRejected);
  const query = useQuery({
    queryKey: ["documents"],
    queryFn: async () => {
      const { data } = await documentApi.getDocuments();
      return data || [];
    },
  });

  const applicationQuery = useQuery({
    queryKey: ["documents-application-status"],
    queryFn: async () => {
      const { data } = await studentApi.getApplication();
      return data || {};
    },
  });

  const cards = useMemo(() => mapDocuments(query.data), [query.data]);
  const isSubmitted =
    Boolean(applicationQuery.data?.status) && applicationQuery.data?.status !== "draft";
  const uploadedCount = cards.filter((card) => card.status !== "not_uploaded").length;
  const summaryType = getSummaryType(cards);

  useFocusEffect(
    React.useCallback(() => {
      query.refetch();
      if (highlightRejected) {
        navigation.setParams({ highlightRejected: false });
      }
    }, [query.refetch, highlightRejected, navigation])
  );

  if (query.isLoading) {
    return <Spinner fullScreen size="large" />;
  }

  const progressPercent = Math.round((uploadedCount / REQUIRED_DOCUMENTS.length) * 100);

  return (
    <ScreenWrapper scroll={false} padded={false}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={query.isRefetching} onRefresh={query.refetch} />
        }
      >
        <Header title="Documents" subtitle="Manage your required uploads" />

        <Card style={styles.progressCard}>
          <Text style={styles.progressTitle}>Upload Progress: {uploadedCount}/4 complete</Text>
          <Text style={styles.progressText}>{uploadedCount} of 4 documents uploaded</Text>
          <View style={styles.progressTrack}>
            <View style={[styles.progressFill, { width: `${progressPercent}%` }]} />
          </View>
        </Card>

        {cards.map((item) => (
          <DocumentCard
            key={item.key}
            item={item}
            highlightRejected={highlightRejected}
            isSubmitted={isSubmitted}
            onAction={() => {
              if (item.status === "not_uploaded") {
                if (isSubmitted) {
                  return;
                }
                navigation.navigate(ROUTES.DOCUMENTS.UPLOAD, {
                  mode: "upload",
                  documentType: item.key,
                });
                return;
              }
              if (item.status === "rejected") {
                navigation.navigate(ROUTES.DOCUMENTS.UPLOAD, {
                  mode: "reupload",
                  documentId: item.id,
                  documentType: item.key,
                  rejectionReason: item.rejectionReason,
                });
                return;
              }
              navigation.navigate(ROUTES.DOCUMENTS.OCR_RESULT, { documentId: item.id });
            }}
          />
        ))}

        {summaryType === "complete" ? (
          <Card style={[styles.summaryCard, styles.completeBanner]}>
            <Text style={styles.completeText}>All documents uploaded</Text>
          </Card>
        ) : null}
        {summaryType === "missing" ? (
          <Card style={[styles.summaryCard, styles.missingBanner]}>
            <Text style={styles.missingText}>
              Upload remaining documents to submit application
            </Text>
          </Card>
        ) : null}
        {summaryType === "rejected" ? (
          <Card style={[styles.summaryCard, styles.rejectedBanner]}>
            <Text style={styles.rejectedText}>
              Action required: Re-upload rejected documents
            </Text>
          </Card>
        ) : null}
      </ScrollView>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  progressCard: {
    marginBottom: spacing.md,
  },
  progressTitle: {
    fontSize: fontSize.lg,
    color: colors.text,
    fontWeight: "700",
    marginBottom: spacing.xs,
  },
  progressText: {
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  progressTrack: {
    height: 8,
    borderRadius: 999,
    backgroundColor: colors.border,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    backgroundColor: colors.primary,
  },
  card: {
    marginBottom: spacing.md,
  },
  highlightRejectedCard: {
    borderColor: colors.danger,
    borderWidth: 2,
    backgroundColor: "#FEF2F2",
  },
  cardHeader: {
    marginBottom: spacing.sm,
  },
  docTitle: {
    fontSize: fontSize.lg,
    color: colors.text,
    fontWeight: "700",
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.xs,
  },
  statusText: {
    marginLeft: spacing.xs,
    fontWeight: "600",
  },
  confidence: {
    marginLeft: spacing.xs,
    color: colors.textSecondary,
  },
  metaText: {
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  rejection: {
    color: colors.danger,
    marginBottom: spacing.xs,
  },
  actionWrap: {
    marginTop: spacing.sm,
  },
  lockHint: {
    color: colors.textSecondary,
    fontWeight: "600",
  },
  summaryCard: {
    marginTop: spacing.sm,
  },
  completeBanner: {
    backgroundColor: "#DCFCE7",
    borderColor: colors.success,
  },
  missingBanner: {
    backgroundColor: "#FEF3C7",
    borderColor: colors.warning,
  },
  rejectedBanner: {
    backgroundColor: "#FEE2E2",
    borderColor: colors.danger,
  },
  completeText: {
    color: colors.success,
    fontWeight: "700",
  },
  missingText: {
    color: colors.warning,
    fontWeight: "700",
  },
  rejectedText: {
    color: colors.danger,
    fontWeight: "700",
  },
});

export default DocumentListScreen;
