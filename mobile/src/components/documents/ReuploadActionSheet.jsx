import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Modal, StyleSheet, Alert } from 'react-native';
import { Camera, Image as ImageIcon, File } from 'lucide-react-native';
import { pickFromCamera, pickFromGallery, pickPDF, pickAndValidate } from '../../utils/filePicker';

const IMAGE_DOCUMENT_ TYPES = ['aadhar', 'marksheet_10', 'marksheet_12', 'rank_card'];

export function ReuploadActionSheet({ visible, onClose, onPicked, originalDocumentType }) {
  const handlePick = async (source) => {
    const asset = await pickAndValidate(source);
    
    if (!asset) return;
    
    const isPdf = asset.type === 'application/pdf';
    const isImageDoc = originalDocumentType && IMAGE_DOCUMENT_TYPES.includes(originalDocumentType);
    
    if (isPdf && isImageDoc) {
      Alert.alert(
        'Different file type',
        'The original was an image. Are you sure you want to upload a PDF?',
        [
          { text: 'Cancel', style: 'cancel', onPress: () => {} },
          { text: 'Continue', onPress: () => { onClose(); onPicked(asset); } },
        ]
      );
      return;
    }
    
    onClose();
    if (asset) onPicked(asset);
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <TouchableOpacity style={styles.backdrop} onPress={onClose} activeOpacity={1}>
        <View style={styles.sheet}>
          <Text style={styles.title}>Re-upload Document</Text>

          <TouchableOpacity style={styles.option} onPress={() => handlePick(pickFromCamera)}>
            <Camera size={24} color="#2563EB" />
            <Text style={styles.optionText}>Take Photo</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.option} onPress={() => handlePick(pickFromGallery)}>
            <ImageIcon size={24} color="#2563EB" />
            <Text style={styles.optionText}>Choose from Gallery</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.option} onPress={() => handlePick(pickPDF)}>
            <File size={24} color="#2563EB" />
            <Text style={styles.optionText}>Pick PDF</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.cancel} onPress={onClose}>
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  sheet: { backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 20 },
  title: { fontSize: 18, fontWeight: '600', marginBottom: 16, textAlign: 'center' },
  option: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12 },
  optionText: { fontSize: 16, color: '#111827' },
  cancel: { padding: 16, alignItems: 'center', marginTop: 8 },
  cancelText: { fontSize: 16, color: '#EF4444', fontWeight: '500' },
});

export default ReuploadActionSheet;
