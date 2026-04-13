import React, { useEffect, useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useQuery } from "@tanstack/react-query";
import { Feather } from "@expo/vector-icons";

import Spinner from "../../components/ui/Spinner";
import { documentApi } from "../../services/documentApi";
import { colors, fontSize, spacing } from "../../theme";

let ImageZoomViewer = null;
let PdfViewer = null;
try {
  ImageZoomViewer = require("react-native-image-zoom-viewer").default;
} catch {
  ImageZoomViewer = null;
}
try {
  PdfViewer = require("react-native-pdf").default;
} catch {
  PdfViewer = null;
}

const getDocLabel = (value) =>
  String(value || "Document")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (m) => m.toUpperCase());

const DocumentViewerScreen = ({ route, navigation }) => {
  const documentId = route?.params?.documentId || null;
  const [token, setToken] = useState(null);

  const detailQuery = useQuery({
    queryKey: ["document-viewer-detail", documentId],
    queryFn: async () => {
      if (!documentId) {
        return null;
      }
      const { data } = await documentApi.getDetail(documentId);
      return data || null;
    },
    enabled: Boolean(documentId),
  });

  useEffect(() => {
    const loadToken = async () => {
      const stored = await AsyncStorage.getItem("auth_token");
      setToken(stored || null);
    };
    loadToken();
  }, []);

  if (detailQuery.isLoading) {
    return (
      <View style={styles.loadingRoot}>
        <Spinner size="large" color={colors.surface} />
      </View>
    );
  }

  const detail = detailQuery.data || {};
  const docTypeLabel = getDocLabel(detail.document_type);
  const filePath = String(detail.file_path || "").toLowerCase();
  const mime = String(detail.mime_type || "").toLowerCase();
  const isPdf = mime.includes("pdf") || filePath.endsWith(".pdf");
  const fileUri = documentApi.getFileUrl(documentId);
  const headers = token ? { Authorization: `Token ${token}` } : {};

  const imageUrls = useMemo(
    () => [
      {
        url: fileUri,
        headers,
      },
    ],
    [fileUri, token]
  );

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>{docTypeLabel}</Text>
        <Pressable onPress={() => navigation.goBack()} style={styles.closeBtn}>
          <Feather name="x" size={22} color={colors.surface} />
        </Pressable>
      </View>

      <View style={styles.viewerArea}>
        {isPdf ? (
          PdfViewer ? (
            <PdfViewer
              source={{ uri: fileUri, headers }}
              style={styles.viewer}
              trustAllCerts
              enablePaging
              horizontal={false}
              fitPolicy={2}
            />
          ) : (
            <View style={styles.fallbackWrap}>
              <Text style={styles.fallbackText}>
                PDF viewer dependency missing. Install react-native-pdf.
              </Text>
            </View>
          )
        ) : ImageZoomViewer ? (
          <ImageZoomViewer
            imageUrls={imageUrls}
            enableSwipeDown={false}
            saveToLocalByLongPress={false}
            backgroundColor="#000000"
          />
        ) : (
          <View style={styles.fallbackWrap}>
            <Text style={styles.fallbackText}>
              Image zoom viewer dependency missing. Install react-native-image-zoom-viewer.
            </Text>
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#000000",
  },
  loadingRoot: {
    flex: 1,
    backgroundColor: "#000000",
    alignItems: "center",
    justifyContent: "center",
  },
  header: {
    paddingTop: spacing.xl,
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.sm,
    backgroundColor: "#000000",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  headerTitle: {
    color: colors.surface,
    fontSize: fontSize.lg,
    fontWeight: "700",
  },
  closeBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.15)",
  },
  viewerArea: {
    flex: 1,
    backgroundColor: "#000000",
  },
  viewer: {
    flex: 1,
    width: "100%",
    backgroundColor: "#000000",
  },
  fallbackWrap: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
  },
  fallbackText: {
    color: colors.surface,
    textAlign: "center",
    fontSize: fontSize.md,
  },
});

export default DocumentViewerScreen;
