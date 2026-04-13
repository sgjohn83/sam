import api from "./api";

export const studentApi = {
  getAutofill: () => api.get("/student/autofill/"),
  getProfileCompletion: () => api.get("/student/profile/completion/"),
  getProfile: () => api.get("/student/profile/"),
  createProfile: (payload) => api.post("/student/profile/", payload),
  updateProfile: (payload) => api.put("/student/profile/", payload),
  savePushToken: (payload) => api.post("/student/push-token/", payload),
  getStatus: () => api.get("/student/status/"),
  getRejectedDocuments: () => api.get("/student/rejected-documents/"),

  // Branches
  getBranches: () => api.get("/branches/"),

  // Application
  getApplication: () => api.get("/student/application/"),
  saveBranchPreferences: (ids) =>
    api.put("/student/application/branch-preferences/", { branch_ids: ids }),
  submitApplication: () => api.post("/student/application/submit/"),
  getStatusTimeline: () => api.get("/student/application/status/"),
  uploadPaymentProof: (file) => {
    const formData = new FormData();
    formData.append("file", {
      uri: file.uri,
      type: file.type,
      name: file.fileName,
    });
    return api.post("/student/application/payment-proof/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

export default studentApi;
