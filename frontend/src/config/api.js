// Configuration de l'API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const API_ENDPOINTS = {
  // Authentication
  LOGIN: `${API_BASE_URL}/auth/login/`,
  REFRESH_TOKEN: `${API_BASE_URL}/auth/token/refresh/`,
  
  // Plans
  PLANS: `${API_BASE_URL}/subscriptions/plans/`,
  
  // Payments
  PAYMENTS: `${API_BASE_URL}/payments/`,
  
  // User
  USER_PROFILE: `${API_BASE_URL}/users/profile/`,
};

export default API_BASE_URL; 