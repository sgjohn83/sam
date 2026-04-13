import React, { useState } from "react";
import {
  FlatList,
  StyleSheet,
  Text,
  View,
  RefreshControl,
} from "react-native";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigation } from "@react-navigation/native";
import { Feather } from "@expo/vector-icons";
import Toast from "react-native-toast-message";
import NetInfo from "@react-native-community/netinfo";

import Header from "../../components/layout/Header";
import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Spinner from "../../components/ui/Spinner";
import studentApi from "../../services/studentApi";
import { documentApi } from "../../services/documentApi";
import ReuploadActionSheet from "../../components/documents/ReuploadActionSheet";
import RejectedDocumentCard from "../../components/documents/RejectedDocumentCard";
import { colors, fontSize, spacing } from "../../theme";

const EmptyState = () => (
  <View style={styles.emptyContainer}>
    <Feather name="check-circle" size={64} color={colors.success} />
    <Text style={styles.emptyTitle}>All Good!</Text>
    <Text style={styles.emptyText}>No documents need re-upload</Text>
  </View>
);

const RejectedDocumentsScreen = () => {
  const navigation = useNavigation();
  const route = useRoute();
  const queryClient = useQueryClient();
  const [activeDocId, setActiveDocId] = useState(null);
  const [sheetVisible, setSheetVisible] = useState(false);
  const [uploadingId, setUploadingId] = useState(null);

  const query = useQuery({
    queryKey: ["rejected-documents"],
    queryFn: async () => {
      const { data } = await studentApi.getRejectedDocuments();
      return data?.documents || [];
    },
  });

  const reuploadMutation = useMutation({
    mutationFn: async ({ id, asset }) => {
      const netInfo = await NetInfo.fetch();
      if (!netInfo.isConnected) {
        throw new Error('NETWORK_OFFLINE');
      }
      
      try {
        const res = await documentApi.reupload(id, asset);
        return { data: res.data, success: true };
      } catch (error) {
        if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
          const pollRes = await documentApi.getDetail(id);
          if (pollRes.data?.status === 'extracted') {
            return { data: pollRes.data, success: true, polled: true };
          }
        }
        throw error;
      }
    },
    onMutate: ({ id }) => setUploadingId(id),
    onSuccess: (result) => {
      const confidence = result.data?.overall_confidence || 0;
      const confidencePercent = Math.round(confidence * 100);
      
      let message = `Processed with ${confidencePercent}% confidence`;
      if (confidence < 0.80) {
        message += '. Consider retaking with better lighting.';
      }
      
      Toast.show({
        type: 'success',
        text1: 'Document re-uploaded',
        text2: message,
      });
      queryClient.invalidateQueries({ queryKey: ['rejected-documents'] });
      queryClient.invalidateQueries({ queryKey: ['rejected-count'] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      
      query.refetch().then((result) => {
        if (!result.data?.length) {
          navigation.goBack();
        }
      });
    },
    onError: (err) => {
      if (err.message === 'NETWORK_OFFLINE') {
        Toast.show({ type: 'error', text1: "You're offline", text2: 'Check your connection and try again.' });
        return;
      }
      const msg = err.response?.data?.error || 'Upload failed. Please try again.';
      Toast.show({ type: 'error', text1: 'Re-upload failed', text2: msg });
    },
    onSettled: () => setUploadingId(null),
  });
      queryClient.invalidateQueries({ queryKey: ['rejected-documents'] });
      queryClient.invalidateQueries({ queryKey: ['rejected-count'] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      
      query.refetch().then((result) => {
        if (!result.data?.length) {
          navigation.goBack();
        }
      });
    },
    onError: (err) => {
      const msg = err.response?.data?.error || 'Upload failed. Please try again.';
      Toast.show({ type: 'error', text1: 'Re-upload failed', text2: msg });
    },
    onSettled: () => setUploadingId(null),
  });

  const handleReuploadPress = (documentId) => {
    setActiveDocId(documentId);
    setSheetVisible(true);
  };

  const handlePicked = (asset) => {
    if (activeDocId) {
      reuploadMutation.mutate({ id: activeDocId, asset });
    }
  };

  if (query.isLoading) {
    return <Spinner fullScreen size="large" />;
  }

  const documents = query.data || [];

  return (
    <ScreenWrapper scroll={false} padded={false}>
      <FlatList
        data={documents}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={query.isRefetching}
            onRefresh={query.refetch}
            colors={[colors.primary]}
          />
        }
        ListHeaderComponent={
          <Header
            title="Document Alerts"
            subtitle="Documents that need re-upload"
          />
        }
        ListEmptyComponent={<EmptyState />}
        renderItem={({ item }) => (
          <RejectedDocumentCard
            item={item}
            isUploading={uploadingId === item.id}
            onReupload={() => handleReuploadPress(item.id)}
          />
        )}
      />

      <ReuploadActionSheet
        visible={sheetVisible}
        onClose={() => setSheetVisible(false)}
        onPicked={handlePicked}
      />
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  card: {
    marginBottom: spacing.md,
    borderWidth: 2,
    borderColor: colors.danger,
    backgroundColor: "#FEF2F2",
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.sm,
  },
  docType: {
    fontSize: fontSize.lg,
    fontWeight: "700",
    color: colors.text,
    marginLeft: spacing.sm,
  },
  categoryRow: {
    flexDirection: "row",
    marginBottom: spacing.sm,
  },
  categoryLabel: {
    fontSize: fontSize.sm,
    color: colors.textSecondary,
  },
  categoryValue: {
    fontSize: fontSize.sm,
    fontWeight: "600",
    color: colors.danger,
  },
  reasonBox: {
    backgroundColor: "white",
    padding: spacing.sm,
    borderRadius: 8,
    marginBottom: spacing.sm,
  },
  reasonLabel: {
    fontSize: fontSize.sm,
    fontWeight: "600",
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  reasonText: {
    fontSize: fontSize.sm,
    color: colors.text,
    lineHeight: 20,
  },
  dateText: {
    fontSize: fontSize.sm,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  actionWrap: {
    marginTop: spacing.sm,
  },
  emptyContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: spacing.xl * 2,
  },
  emptyTitle: {
    fontSize: fontSize.xl,
    fontWeight: "700",
    color: colors.success,
    marginTop: spacing.md,
  },
  emptyText: {
    fontSize: fontSize.md,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
});

export default RejectedDocumentsScreen;
