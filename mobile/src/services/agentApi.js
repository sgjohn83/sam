import api from './api';

export const agentApi = {
  getDashboard: () => api.get('/agents/dashboard/'),
  getCompletionStatus: () => api.get('/agents/profile/completion-status/'),
  getPipelineSummary: () => api.get('/agents/pipeline-summary/'),
  getStudents: (params) => api.get('/agents/students/', { params }),
  getStudentDetail: (id) => api.get(`/agents/students/${id}/`),
  registerStudent: (data) => api.post('/agents/register-student/', data),
  getCommissions: (params) => api.get('/agents/commissions/', { params }),
  getCommissionSummary: () => api.get('/agents/commission-summary/'),
  getProfile: () => api.get('/agents/profile/'),
  updateProfile: (data) => api.patch('/agents/profile/', data),
};
