import React, { useMemo } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { Feather } from "@expo/vector-icons";

import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { documentApi } from "../../services/documentApi";
import { ROUTES } from "../../constants/routes";
import { colors, fontSize, spacing } from "../../theme";

const toTitle = (value) =>
  String(value || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (ch) => ch.toUpperCase());

const stringifyValue = (value) => {
  if (value === null || value === undefined) {
    return "(empty)";
  }
  if (typeof value === "string") {
    return value.trim() ? value : "(empty)";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
};

const getFieldConfidenceMeta = (score, value) => {
  if (score === 0 || value === "(empty)") {
    return { icon: "circle", color: colors.danger, label: "missing" };
  }
  if (score >= 0.9) {
    return { icon: "disc", color: colors.success, label: "high" };
  }
  if (score >= 0.7) {
    return { icon: "minus-circle", color: colors.warning, label: "medium" };
  }
  return { icon: "circle", color: colors.danger, label: "low" };
};

const getOverallLabel = (score) => {
  if (score >= 0.9) {
    return { text: "High", color: colors.success };
  }
  if (score >= 0.7) {
    return { text: "Medium", color: colors.warning };
  }
  return { text: "Low", color: colors.danger };
};

const OCRResultScreen = ({ route, navigation }) => {
  const uploadResponse = route?.params?.uploadResponse || null;
  const documentId = route?.params?.documentId || uploadResponse?.id || null;
  const warning = route?.params?.warning || uploadResponse?.ocr_warning || null;

  const ocrQuery = useQuery({
    queryKey: ["ocr-result", documentId],
    queryFn: async () => {
      if (!documentId) {
        return null;
      }
      const { data } = await documentApi.getOCRResult(documentId);
      return data || null;
    },
    enabled: Boolean(documentId),
  });

  const detailQuery = useQuery({
    queryKey: ["document-detail", documentId],
    queryFn: async () => {
      if (!documentId) {
        return null;
      }
      const { data } = await documentApi.getDetail(documentId);
      return data || null;
    },
    enabled: Boolean(documentId),
  });

  if (ocrQuery.isLoading || detailQuery.isLoading) {
    return <Spinner fullScreen size="large" />;
  }

  const ocr = ocrQuery.data;
  const detail = detailQuery.data || uploadResponse || {};
  const docLabel = toTitle(detail?.document_type || "Document");

  const extractedFields = ocr?.extracted_fields || uploadResponse?.ocr_result?.extracted_fields || {};
  const confidenceScores = ocr?.confidence_scores || uploadResponse?.ocr_result?.confidence_scores || {};
  const overallConfidence =
    ocr?.overall_confidence ?? uploadResponse?.ocr_result?.overall_confidence ?? 0;
  const overallPct = Math.round(overallConfidence * 100);
  const overallMeta = getOverallLabel(overallConfidence);

  const rows = useMemo(
    () =>
      Object.keys(extractedFields).map((key) => {
        const value = stringifyValue(extractedFields[key]);
        const scoreRaw = confidenceScores[key];
        const score = typeof scoreRaw === "number" ? scoreRaw : 0;
        return {
          key,
          label: toTitle(key),
          value,
          score,
          meta: getFieldConfidenceMeta(score, value),
        };
      }),
    [extractedFields, confidenceScores]
  );

  const missingRows = rows.filter((row) => row.score === 0 || row.value === "(empty)");
  const missingCount = missingRows.length;

  const handleViewOriginal = () => {
    if (!documentId) {
      return;
    }
    navigation.navigate(ROUTES.DOCUMENTS.VIEWER, { documentId });
  };

  return (
    <ScreenWrapper scroll={false} padded={false}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.backLink} onPress={() => navigation.goBack()}>
          Back
        </Text>
        <Text style={styles.title}>{docLabel} Results</Text>

        <View style={styles.confidenceWrap}>
          <Text style={styles.confidenceLabel}>Confidence:</Text>
          <Text style={[styles.confidenceValue, { color: overallMeta.color }]}>
            {overallPct}% {overallMeta.text}
          </Text>
        </View>

        {warning || missingCount > 0 ? (
          <Card style={styles.warningCard}>
            <Text style={styles.warningText}>
              Some fields could not be extracted automatically. You can fill them manually.
            </Text>
          </Card>
        ) : null}

        <Text style={styles.sectionTitle}>Extracted Fields</Text>
        {rows.length === 0 ? (
          <Card>
            <Text style={styles.emptyText}>No extracted fields available.</Text>
          </Card>
        ) : (
          rows.map((row) => (
            <Card key={row.key} style={styles.fieldCard}>
              <View style={styles.fieldHead}>
                <Text style={styles.fieldName}>{row.label}</Text>
                <View style={styles.scoreWrap}>
                  <Feather name={row.meta.icon} size={14} color={row.meta.color} />
                  <Text style={[styles.scoreText, { color: row.meta.color }]}>
                    {row.score.toFixed(2)}
                  </Text>
                </View>
              </View>
              <Text style={styles.fieldValue}>{row.value}</Text>
            </Card>
          ))
        )}

        {missingCount > 0 ? (
          <Text style={styles.missingText}>
            {missingCount} field{missingCount > 1 ? "s" : ""} could not be extracted
            {missingRows.length ? ` (${missingRows.map((f) => f.label).join(", ")})` : ""}. You can
            fill {missingCount > 1 ? "them" : "it"} manually in the application form.
          </Text>
        ) : null}

        <View style={styles.actionSpacing}>
          <Button title="View Original Document" variant="secondary" onPress={handleViewOriginal} />
        </View>
        <Button
          title="Looks Good  Continue"
          onPress={() => navigation.navigate(ROUTES.DOCUMENTS.LIST)}
        />
      </ScrollView>
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  backLink: {
    color: colors.primary,
    fontWeight: "600",
    marginBottom: spacing.sm,
  },
  title: {
    color: colors.text,
    fontSize: fontSize.xl,
    fontWeight: "700",
    marginBottom: spacing.sm,
  },
  confidenceWrap: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.md,
  },
  confidenceLabel: {
    color: colors.textSecondary,
    fontSize: fontSize.md,
    marginRight: spacing.sm,
  },
  confidenceValue: {
    fontSize: fontSize.lg,
    fontWeight: "700",
  },
  warningCard: {
    backgroundColor: "#FEF3C7",
    borderColor: colors.warning,
    marginBottom: spacing.md,
  },
  warningText: {
    color: "#92400E",
  },
  sectionTitle: {
    color: colors.text,
    fontSize: fontSize.lg,
    fontWeight: "700",
    marginBottom: spacing.sm,
  },
  fieldCard: {
    marginBottom: spacing.sm,
  },
  fieldHead: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: spacing.xs,
  },
  fieldName: {
    color: colors.textSecondary,
    fontWeight: "600",
  },
  scoreWrap: {
    flexDirection: "row",
    alignItems: "center",
  },
  scoreText: {
    marginLeft: 6,
    fontWeight: "700",
    fontSize: fontSize.sm,
  },
  fieldValue: {
    color: colors.text,
    fontSize: fontSize.md,
  },
  emptyText: {
    color: colors.textSecondary,
  },
  missingText: {
    marginTop: spacing.sm,
    marginBottom: spacing.md,
    color: colors.textSecondary,
  },
  actionSpacing: {
    marginBottom: spacing.sm,
  },
});

export default OCRResultScreen;
