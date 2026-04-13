import api from "./api";

export const documentApi = {
  // List student's documents (4 max)
  getDocuments: () => api.get("/documents/"),

  // Upload new document (multipart)
  upload: (documentType, file) => {
    const formData = new FormData();
    formData.append("document_type", documentType);
    formData.append("file", {
      uri: file.uri,
      type: file.type,
      name: file.fileName || file.name || "document",
    });
    return api.post("/documents/upload/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
  },

  // Re-upload rejected document
  reupload: async (documentId, fileAsset) => {
    const formData = new FormData();
    formData.append("file", {
      uri: fileAsset.uri,
      name: fileAsset.name || `reupload_${Date.now()}.jpg`,
      type: fileAsset.mimeType || "image/jpeg",
    });

    return api.post(`/documents/${documentId}/reupload/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 60000, // OCR runs synchronously
    });
  },

  // Get document detail with OCR result
  getDetail: (documentId) => api.get(`/documents/${documentId}/`),

  // Get latest OCR result with full extracted fields
  getOCRResult: (documentId) => api.get(`/documents/${documentId}/ocr-result/`),

  // Get document file (image/PDF) for preview
  getFileUrl: (documentId) => `${api.defaults.baseURL}/documents/${documentId}/file/`,

  // Get auto-fill data from all documents
  getAutofill: () => api.get("/student/autofill/"),

  // Get rejected documents count (lightweight)
  getRejectedCount: () => api.get("/students/me/rejected-documents/count/"),
};

export default documentApi;
