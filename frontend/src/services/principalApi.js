import api from './api';

export const principalApi = {
  getAdmissionStats: () => api.get('/principal/stats/admissions/'),
  getSeatStats: () => api.get('/principal/stats/seats/'),
  getRevenueStats: () => api.get('/principal/stats/revenue/'),
  getAgentPerformance: () => api.get('/principal/stats/agents/'),
  getVerificationPerformance: () => api.get('/principal/stats/verification/'),
  getAdmissionTrend: (params) => api.get('/principal/stats/trend/', { params }),
  getAuditTrail: (params) => api.get('/principal/audit-trail/', { params }),
  getAuditTrailActions: () => api.get('/principal/audit-trail/actions/'),
  exportAuditTrail: (params) =>
    api.get('/principal/audit-trail/export/', {
      params,
      responseType: 'blob',
    }),
  getAdminCommissions: (params) => api.get('/agents/commissions/admin/', { params }),
  getAdminAgents: () => api.get('/agents/admin/'),
  approveCommission: (commissionId) => api.post(`/agents/commissions/${commissionId}/approve/`),
  rejectCommission: (commissionId, data) => api.post(`/agents/commissions/${commissionId}/reject/`, data),
  markCommissionPaid: (commissionId, data) => api.post(`/agents/commissions/${commissionId}/mark-paid/`, data),
  bulkPayCommissions: (data) => api.post('/agents/commissions/bulk-pay/', data),
};

