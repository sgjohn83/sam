import React, { useMemo, useState } from "react";
import {
  Image,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { Feather } from "@expo/vector-icons";
import { useQuery } from "@tanstack/react-query";
import Toast from "react-native-toast-message";

import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Spinner from "../../components/ui/Spinner";
import { DOCUMENT_TYPES } from "../../constants/documentTypes";
import { ROUTES } from "../../constants/routes";
import { documentApi } from "../../services/documentApi";
import studentApi from "../../services/studentApi";
import { pickFromCamera, pickFromGallery, pickPDF, validateFile } from "../../utils/filePicker";
import { colors, fontSize, spacing } from "../../theme";

const formatBytes = (size) => {
  if (!size) {
    return "Unknown size";
  }
  const mb = size / (1024 * 1024);
  return `${mb.toFixed(2)} MB`;
};

const DocumentUploadScreen = ({ route, navigation }) => {
  const documentTypeParam = route?.params?.documentType;
  const mode = route?.params?.mode || "upload";
  const documentId = route?.params?.documentId || null;
  const rejectionReason = route?.params?.rejectionReason || null;
  const isReupload = mode === "reupload" && Boolean(documentId);

  const documentConfig = useMemo(
    () => DOCUMENT_TYPES.find((item) => item.key === documentTypeParam) || DOCUMENT_TYPES[0],
    [documentTypeParam]
  );

  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const applicationQuery = useQuery({
    queryKey: ["document-upload-application-status"],
    queryFn: async () => {
      const { data } = await studentApi.getApplication();
      return data || {};
    },
  });
  const isApplicationLocked =
    Boolean(applicationQuery.data?.status) && applicationQuery.data?.status !== "draft";
  const isUploadLocked = isApplicationLocked && !isReupload;

  const onPick = async (pickerFn) => {
    if (isUploadLocked) {
      return;
    }
    try {
      const file = await pickerFn();
      if (!file) {
        return;
      }

      const validation = validateFile(file);
      if (!validation.valid) {
        Toast.show({
          type: "error",
          text1: "Invalid file",
          text2: validation.error,
        });
        return;
      }

      setSelectedFile(file);
    } catch (error) {
      Toast.show({
        type: "error",
        text1: "File selection failed",
        text2: error?.message || "Please try again.",
      });
    }
  };

  const onUpload = async () => {
    if (!selectedFile || isUploading || isUploadLocked) {
      return;
    }

    setIsUploading(true);
    try {
      const response = isReupload
        ? await documentApi.reupload(documentId, selectedFile)
        : await documentApi.upload(documentConfig.key, selectedFile);

      const payload = response?.data || {};
      const warning = payload?.ocr_warning || null;

      navigation.replace(ROUTES.DOCUMENTS.OCR_RESULT, {
        documentId: payload?.id || documentId || null,
        uploadResponse: payload,
        warning,
      });
    } catch (error) {
      const message =
        error?.response?.data?.detail ||
        error?.response?.data?.error ||
        "Upload failed. Please try again.";

      Toast.show({
        type: "error",
        text1: "Upload failed",
        text2: message,
      });
    } finally {
      setIsUploading(false);
    }
  };

  const isPdf = selectedFile?.type === "application/pdf";

  return (
    <ScreenWrapper scroll={false} padded={false}>
      <ScrollView contentContainerStyle={styles.content}>
        <Pressable onPress={() => navigation.goBack()}>
        <Text style={styles.backLink}>Back</Text>
        </Pressable>

        <Text style={styles.title}>
          {isReupload ? `Re-upload ${documentConfig.label}` : `Upload ${documentConfig.label}`}
        </Text>

        {isReupload && rejectionReason ? (
          <Card style={styles.rejectionCard}>
            <Text style={styles.rejectionTitle}>Action Required</Text>
            <Text style={styles.rejectionText}>Reason: "{rejectionReason}"</Text>
          </Card>
        ) : null}

        {isUploadLocked ? (
          <Card style={styles.lockCard}>
            <Text style={styles.lockText}>
              Document uploads are locked after application submission. Re-upload is allowed only
              for rejected documents.
            </Text>
          </Card>
        ) : null}

        <Card style={styles.previewCard}>
          <Pressable
            onPress={() => onPick(isPdf ? pickPDF : pickFromGallery)}
            style={styles.previewArea}
          >
            {selectedFile ? (
              isPdf ? (
                <View style={styles.pdfPreview}>
                  <Feather name="file-text" size={42} color={colors.primary} />
                  <Text style={styles.previewName}>{selectedFile.fileName}</Text>
                  <Text style={styles.previewMeta}>{formatBytes(selectedFile.fileSize)}</Text>
                </View>
              ) : (
                <Image source={{ uri: selectedFile.uri }} style={styles.previewImage} />
              )
            ) : (
              <View style={styles.emptyPreview}>
                <Feather name="image" size={44} color={colors.textSecondary} />
                <Text style={styles.emptyPreviewText}>Document preview area</Text>
              </View>
            )}
          </Pressable>
          <Text style={styles.changeText}>Tap to change</Text>
        </Card>

        <Card style={styles.infoCard}>
          <Text style={styles.sectionTitle}>Tips:</Text>
          {documentConfig.tips.map((tip) => (
            <Text key={tip} style={styles.tipText}>
              {`\u2022 ${tip}`}
            </Text>
          ))}
          <Text style={styles.metaText}>Accepted formats: {documentConfig.acceptedFormats}</Text>
          <Text style={styles.metaText}>Max file size: 5 MB</Text>
        </Card>

        <View style={styles.pickerRow}>
          <View style={styles.pickerBtn}>
            <Button
              title="Camera"
              variant="secondary"
              onPress={() => onPick(pickFromCamera)}
              disabled={isUploadLocked}
            />
          </View>
          <View style={styles.pickerBtn}>
            <Button
              title="Gallery"
              variant="secondary"
              onPress={() => onPick(pickFromGallery)}
              disabled={isUploadLocked}
            />
          </View>
          <View style={styles.pickerBtn}>
            <Button
              title="PDF"
              variant="secondary"
              onPress={() => onPick(pickPDF)}
              disabled={isUploadLocked}
            />
          </View>
        </View>

        <Button
          title={isReupload ? "Re-upload Document" : "Upload Document"}
          onPress={onUpload}
          disabled={!selectedFile || isUploading || isUploadLocked}
        />
      </ScrollView>

      <Modal visible={isUploading} transparent animationType="fade">
        <View style={styles.loadingOverlay}>
          <View style={styles.loadingCard}>
            <Spinner size="large" />
            <Text style={styles.loadingText}>Uploading and processing document...</Text>
          </View>
        </View>
      </Modal>
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
    fontSize: fontSize.xl,
    color: colors.text,
    fontWeight: "700",
    marginBottom: spacing.md,
  },
  previewCard: {
    marginBottom: spacing.md,
  },
  previewArea: {
    height: 220,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: "#F3F4F6",
    overflow: "hidden",
    alignItems: "center",
    justifyContent: "center",
  },
  previewImage: {
    width: "100%",
    height: "100%",
    resizeMode: "cover",
  },
  emptyPreview: {
    alignItems: "center",
    justifyContent: "center",
  },
  emptyPreviewText: {
    marginTop: spacing.sm,
    color: colors.textSecondary,
  },
  pdfPreview: {
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
  previewName: {
    marginTop: spacing.sm,
    color: colors.text,
    fontWeight: "600",
    textAlign: "center",
  },
  previewMeta: {
    marginTop: spacing.xs,
    color: colors.textSecondary,
  },
  changeText: {
    marginTop: spacing.sm,
    color: colors.textSecondary,
    textAlign: "center",
  },
  infoCard: {
    marginBottom: spacing.md,
  },
  rejectionCard: {
    marginBottom: spacing.md,
    backgroundColor: "#FEF3C7",
    borderColor: colors.warning,
  },
  rejectionTitle: {
    color: "#92400E",
    fontWeight: "700",
    marginBottom: spacing.xs,
  },
  rejectionText: {
    color: "#92400E",
  },
  lockCard: {
    marginBottom: spacing.md,
    backgroundColor: "#EFF6FF",
    borderColor: colors.primaryLight,
  },
  lockText: {
    color: colors.primary,
    fontWeight: "600",
  },
  sectionTitle: {
    fontWeight: "700",
    color: colors.text,
    marginBottom: spacing.xs,
  },
  tipText: {
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  metaText: {
    marginTop: spacing.xs,
    color: colors.text,
    fontWeight: "600",
  },
  pickerRow: {
    flexDirection: "row",
    marginBottom: spacing.md,
    marginRight: -spacing.sm,
  },
  pickerBtn: {
    flex: 1,
    marginRight: spacing.sm,
  },
  loadingOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.lg,
  },
  loadingCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.lg,
    alignItems: "center",
    minWidth: 260,
  },
  loadingText: {
    marginTop: spacing.md,
    color: colors.text,
    fontSize: fontSize.md,
    textAlign: "center",
  },
});

export default DocumentUploadScreen;
