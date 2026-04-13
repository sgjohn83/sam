import api from "./api";

const authApi = {
  register: (email) => api.post("/accounts/auth/register/", { email }),
  verifyOtp: (payload) => api.post("/accounts/auth/verify-otp/", payload),
  googleLogin: (token) => api.post("/accounts/auth/google/", { token }),
  me: () => api.get("/accounts/auth/me/"),
  logout: () => api.post("/accounts/auth/logout/"),
};

export default authApi;
