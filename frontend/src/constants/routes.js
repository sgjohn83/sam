export const ROUTES = {
  AUTH: {
    LOGIN: '/login',
    REGISTER: '/register',
    VERIFY_OTP: '/verify-otp',
  },
  STUDENT: {
    DASHBOARD: '/student/dashboard',
    APPLICATION: '/student/application',
    DOCUMENTS: '/student/documents',
    STATUS: '/student/status',
  },
  VERIFICATION: {
    QUEUE: '/verification/queue',
    REVIEW: (appId = ':appId') => `/verification/${appId}/review`,
  },
  OFFICER: {
    DASHBOARD: '/officer/dashboard',
    APPLICATIONS: '/officer/applications',
    SEATS: '/officer/seats',
    WALKIN: '/officer/walkin',
  },
  AGENT: {
    DASHBOARD: '/agent/dashboard',
    UPLOAD: '/agent/upload',
    COMMISSION: '/agent/commission',
  },
  PRINCIPAL: {
    DASHBOARD: '/principal/dashboard',
    CONCESSIONS: '/principal/concessions',
    REPORTS: '/principal/reports',
  },
  ADMIN: {
    DASHBOARD: '/admin/dashboard',
    ACADEMIC_YEAR: '/admin/academic-year',
    SEAT_MATRIX: '/admin/seat-matrix',
    FEE_STRUCTURES: '/admin/fee-structures',
    USERS: '/admin/users',
    OCR_HEALTH: '/admin/ocr-health',
    ERP_SYNC: '/admin/erp-sync',
  },
};
