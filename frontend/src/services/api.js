import axios from 'axios';

const configuredApiUrl = (import.meta.env.VITE_API_URL || '').trim();
const API_BASE_URL = import.meta.env.DEV ? '' : configuredApiUrl;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  signup: (data) => api.post('/api/auth/signup', data),
  login: (data) => api.post('/api/auth/login', data),
};

// Dashboard API
export const dashboardAPI = {
  getDashboard: () => api.get('/api/dashboard/'),
};

// Transactions API
export const transactionsAPI = {
  getAll: () => api.get('/api/transactions/'),
  add: (data) => api.post('/api/transactions/add', data),
  addFromSMS: (data) => api.post('/api/transactions/from-sms', data),
  delete: (id) => api.delete(`/api/transactions/${id}`),
  getCategories: () => api.get('/api/transactions/categories'),
  suggestCategory: (data) => api.post('/api/transactions/suggest-category', data),
  provideFeedback: (data) => api.post('/api/transactions/feedback', data),
};

// Analytics API
export const analyticsAPI = {
  getAnalytics: (period = 'monthly') => api.get(`/api/analytics/?period=${period}`),
};

// Profile API
export const profileAPI = {
  get: () => api.get('/api/profile/'),
  update: (data) => api.put('/api/profile/', data),
};

export default api;

