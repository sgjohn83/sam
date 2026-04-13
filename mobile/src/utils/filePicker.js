import { launchCamera, launchImageLibrary } from "react-native-image-picker";
import DocumentPicker from "react-native-document-picker";
import Toast from "react-native-toast-message";

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
const ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"];
const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png"];

const IMAGE_OPTIONS = {
  mediaType: "photo",
  maxWidth: 2048,
  maxHeight: 2048,
  quality: 0.85,
  includeBase64: false,
};

const normalizeFile = (asset) => {
  if (!asset?.uri) {
    return null;
  }
  return {
    uri: asset.uri,
    type: asset.type || "application/octet-stream",
    fileName: asset.fileName || "upload",
    fileSize: asset.fileSize || 0,
  };
};

export function validateFile(file) {
  if (!file?.uri) {
    return { valid: false, error: "Invalid file." };
  }

  if (file.fileSize && file.fileSize > MAX_FILE_SIZE_BYTES) {
    return { valid: false, error: "File size exceeds 10MB." };
  }

  if (file.type && !ALLOWED_TYPES.includes(file.type)) {
    return { valid: false, error: "Only JPG, PNG, or PDF files are allowed." };
  }

  return { valid: true };
}

export async function pickFromCamera() {
  const result = await launchCamera({
    ...IMAGE_OPTIONS,
    cameraType: "back",
  });
  if (result.didCancel) {
    return null;
  }

  const file = normalizeFile(result.assets?.[0]);
  if (!file) {
    return null;
  }

  const validation = validateFile(file);
  if (!validation.valid) {
    throw new Error(validation.error);
  }

  return file;
}

export async function pickFromGallery() {
  const result = await launchImageLibrary(IMAGE_OPTIONS);
  if (result.didCancel) {
    return null;
  }

  const file = normalizeFile(result.assets?.[0]);
  if (!file) {
    return null;
  }

  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    throw new Error("Gallery selection must be JPG or PNG.");
  }

  const validation = validateFile(file);
  if (!validation.valid) {
    throw new Error(validation.error);
  }

  return file;
}

export async function pickPDF() {
  try {
    const picked = await DocumentPicker.pickSingle({
      type: [DocumentPicker.types.pdf],
      copyTo: "cachesDirectory",
    });

    const file = {
      uri: picked.fileCopyUri || picked.uri,
      type: "application/pdf",
      fileName: picked.name || "document.pdf",
      fileSize: picked.size || 0,
    };

    const validation = validateFile(file);
    if (!validation.valid) {
      throw new Error(validation.error);
    }

    return file;
  } catch (error) {
    if (DocumentPicker.isCancel(error)) {
      return null;
    }
    throw error;
  }
}

export { IMAGE_OPTIONS };

export async function pickAndValidate(source) {
  const asset = await source();
  if (!asset) return null;

  if (asset.fileSize > MAX_FILE_SIZE_BYTES) {
    Toast.show({ type: 'error', text1: 'File too large', text2: 'Max 10 MB' });
    return null;
  }

  const allowed = ALLOWED_TYPES;
  if (asset.type && !allowed.includes(asset.type)) {
    Toast.show({ type: 'error', text1: 'Unsupported file type' });
    return null;
  }

  return asset;
}
