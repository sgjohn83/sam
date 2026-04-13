import axios from 'axios';
import toast from 'react-hot-toast';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  withCredentials: true, // Crucial for session-based auth
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login';
    } else if (error.response?.status === 403) {
      toast.error('Access Denied');
    } else if (!error.response) {
      toast.error('Server unreachable');
    }
    return Promise.reject(error);
  }
);

export default api;
