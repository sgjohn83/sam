import api from './api';

export const agentApi = {
  getDashboard: () => api.get('/agents/dashboard/'),
  getStudents: (params) => api.get('/agents/students/', { params }),
  registerStudent: (data) => api.post('/agents/register-student/', data),
  getCommissions: (params) => api.get('/agents/commissions/', { params }),
  getProfile: () => api.get('/agents/profile/'),
  updateProfile: (data) => api.patch('/agents/profile/', data),
};

export const adminCommissionApi = {
  getCommissions: (params) => api.get('/admin/commissions/', { params }),
  approve: (id) => api.post(`/admin/commissions/${id}/approve/`),
  reject: (id, notes) => api.post(`/admin/commissions/${id}/reject/`, { notes }),
  markPaid: (id, ref) => api.post(`/admin/commissions/${id}/mark-paid/`, { payment_reference: ref }),
  bulkPay: (ids, ref) => api.post('/admin/commissions/bulk-pay/', { commission_ids: ids, payment_reference: ref }),
  getAgents: () => api.get('/admin/agents/'),
};
