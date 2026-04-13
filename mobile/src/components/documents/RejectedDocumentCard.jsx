import React from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import Card from '../ui/Card';
import { colors, fontSize, spacing } from '../../theme';

const formatDate = (value) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

export function RejectedDocumentCard({ item, onReupload, isUploading }) {
  return (
    <Card style={styles.card}>
      <View style={styles.cardHeader}>
        <Feather name="alert-circle" size={20} color={colors.danger} />
        <Text style={styles.docType}>{item.document_type_label}</Text>
      </View>

      {item.rejection_category_display && (
        <View style={styles.categoryRow}>
          <Text style={styles.categoryLabel}>Issue: </Text>
          <Text style={styles.categoryValue}>{item.rejection_category_display}</Text>
        </View>
      )}

      {item.rejection_reason && (
        <View style={styles.reasonBox}>
          <Text style={styles.reasonLabel}>Reason:</Text>
          <Text style={styles.reasonText}>{item.rejection_reason}</Text>
        </View>
      )}

      {item.rejected_at && (
        <Text style={styles.dateText}>Rejected on: {formatDate(item.rejected_at)}</Text>
      )}

      {isUploading && (
        <View style={styles.uploadingOverlay}>
          <ActivityIndicator color={colors.primary} size="small" />
          <Text style={styles.uploadingText}>Processing with OCR...</Text>
        </View>
      )}

      <View style={styles.actionWrap}>
        <TouchableOpacity
          style={[styles.reuploadBtn, isUploading && styles.disabled]}
          onPress={onReupload}
          disabled={isUploading}
        >
          {isUploading ? (
            <>
              <ActivityIndicator color="#fff" size="small" />
              <Text style={styles.btnText}>Processing...</Text>
            </>
          ) : (
            <>
              <Feather name="upload" size={16} color="#fff" />
              <Text style={styles.btnText}>Re-upload</Text>
            </>
          )}
        </TouchableOpacity>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    marginBottom: spacing.md,
    borderWidth: 2,
    borderColor: colors.danger,
    backgroundColor: '#FEF2F2',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  docType: {
    fontSize: fontSize.lg,
    fontWeight: '700',
    color: colors.text,
    marginLeft: spacing.sm,
  },
  categoryRow: {
    flexDirection: 'row',
    marginBottom: spacing.sm,
  },
  categoryLabel: {
    fontSize: fontSize.sm,
    color: colors.textSecondary,
  },
  categoryValue: {
    fontSize: fontSize.sm,
    fontWeight: '600',
    color: colors.danger,
  },
  reasonBox: {
    backgroundColor: 'white',
    padding: spacing.sm,
    borderRadius: 8,
    marginBottom: spacing.sm,
  },
  reasonLabel: {
    fontSize: fontSize.sm,
    fontWeight: '600',
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
  uploadingOverlay: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#EEF2FF',
    padding: spacing.sm,
    borderRadius: 8,
    marginBottom: spacing.sm,
    gap: spacing.xs,
  },
  uploadingText: {
    fontSize: fontSize.sm,
    color: colors.primary,
    fontWeight: '500',
  },
  actionWrap: {
    marginTop: spacing.sm,
  },
  reuploadBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.danger,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: 8,
    gap: spacing.xs,
  },
  disabled: {
    backgroundColor: colors.textSecondary,
  },
  btnText: {
    color: '#fff',
    fontSize: fontSize.sm,
    fontWeight: '600',
  },
});

export default RejectedDocumentCard;
