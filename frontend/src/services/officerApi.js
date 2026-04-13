import api from './api';

export const officerApi = {
  /**
   * Get dashboard statistics
   */
  getDashboardStats: () => api.get('/officer/dashboard/stats/'),

  /**
   * Get paginated list of applications
   * @param {Object} params - Filtering and pagination params
   */
  getApplications: (params) => api.get('/officer/applications/', { params }),

  /**
   * Get single application detail
   * @param {string} id - Application UUID
   */
  getApplicationDetail: (id) => api.get(`/officer/applications/${id}/`),

  /**
   * Lock an application
   * @param {string} id - Application UUID
   */
  lockApplication: (id) => api.post(`/applications/${id}/lock/`),

  /**
   * Unlock an application (admin only)
   * @param {string} id - Application UUID
   * @param {string} reason - Reason for unlocking
   */
  unlockApplication: (id, reason) => api.post(`/applications/${id}/unlock/`, { reason }),

  /**
   * Send fee instructions to student
   * @param {string} id - Application UUID
   * @param {number} feeDeadlineDays - Days until fee deadline (default 7)
   */
  sendFeeInstructions: (id, feeDeadlineDays = 7) => 
    api.post(`/officer/${id}/send-fee-instructions/`, { fee_deadline_days: feeDeadlineDays }),

  /**
   * Resend fee instructions
   * @param {string} id - Application UUID
   */
  resendFeeInstructions: (id) => 
    api.post(`/officer/${id}/resend-fee-instructions/`),

  /**
   * Confirm payment and mark as admitted
   * @param {string} id - Application UUID
   * @param {Object} options - Options including override_deadline and payment_proof_path
   */
  confirmPayment: (id, options = {}) => 
    api.post(`/officer/${id}/confirm-payment/`, options),

  /**
   * Calculate fee for an application
   * @param {string} id - Application UUID
   */
  calculateFee: (id) => api.get(`/officer/applications/${id}/calculate-fee/`),
};