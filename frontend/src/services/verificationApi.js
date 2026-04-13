import api from './api';

export const verificationApi = {
    /**
     * Fetch the main verification queue
     * @param {Object} params - Filtering and sorting params (?search, ?status, ?confidence, ?sort)
     */
    getQueue: (params) => api.get('/verification/queue/', { params }),

    /**
     * Fetch summary statistics for the queue dashboard
     */
    getQueueStats: () => api.get('/verification/queue/stats/'),

    /**
     * Fetch applications currently claimed by the logged-in staff member
     */
    getMyClaims: () => api.get('/verification/queue/my-claims/'),

    /**
     * Claim an application for verification
     * @param {string} id - Application UUID
     */
    claimApplication: (id) => api.post(`/verification/queue/${id}/claim/`),

    /**
     * Release a claimed application back to the queue
     * @param {string} id - Application UUID
     */
    releaseApplication: (id) => api.post(`/verification/queue/${id}/release/`),

    /**
     * Fetch split-screen data for an application
     * @param {string} id - Application UUID
     */
    getSplitScreen: (id) => api.get(`/verification/${id}/split-screen/`),

    /**
     * Edit a field value
     * @param {string} appId - Application UUID
     * @param {Object} data - { document_id, field_name, new_value, notes }
     */
    editField: (appId, data) => api.patch(`/verification/${appId}/field/`, data),

    /**
     * Approve a single field
     * @param {string} appId - Application UUID
     * @param {Object} data - { document_id, field_name }
     */
    approveField: (appId, data) => api.post(`/verification/${appId}/field/approve/`, data),

    /**
     * Bulk approve all pending fields in a document
     * @param {string} appId - Application UUID
     * @param {Object} data - { document_id }
     */
    approveAllFields: (appId, data) => api.post(`/verification/${appId}/fields/approve-all/`, data),

    /**
     * Verify an entire document
     * @param {string} appId - Application UUID
     * @param {string} docId - Document UUID
     */
    verifyDocument: (appId, docId) => api.post(`/verification/${appId}/document/${docId}/verify/`),

    /**
     * Get reupload history for a document
     * @param {string} docId - Document UUID
     */
    getReuploadHistory: (docId) => api.get(`/verification/documents/${docId}/reupload-history/`),

    /**
     * Lock an application
     * @param {string} appId - Application UUID
     */
    lockApplication: (appId) => api.post(`/applications/${appId}/lock/`),

    /**
     * Unlock an application (admin only)
     * @param {string} appId - Application UUID
     * @param {string} reason - Reason for unlocking
     */
    unlockApplication: (appId, reason) => api.post(`/applications/${appId}/unlock/`, { reason }),

    /**
     * Get audit logs for an application
     * @param {string} appId - Application UUID
     */
    getAuditLogs: (appId) => api.get(`/verification/applications/${appId}/audit-logs/`),
};