import api from './api';

export const authApi = {
  login: (data) => api.post('/auth/login/', data),
  register: (email) => api.post('/auth/register/', { email }),
  verifyOtp: (data) => api.post('/auth/verify-otp/', data),
  googleLogin: (token) => api.post('/auth/google/', { token }),
  logout: () => api.post('/auth/logout/'),
  getMe: () => api.get('/auth/me/'),
  checkEmail: (email) => api.get('/auth/check-email/', { params: { email } }),
};
