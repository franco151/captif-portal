import axios from 'axios';
import CryptoJS from 'crypto-js';
import { API_ENDPOINTS } from '../config/api';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class AuthService {
  async login(username, password) {
    try {
      const response = await axios.post(`${API_URL}/auth/login/`, {
        username,
        password,
      });
      
      if (response.data.token) {
        localStorage.setItem('user', JSON.stringify(response.data));
      }
      
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  logout() {
    localStorage.removeItem('user');
  }

  register(username, email, password) {
    return axios.post(`${API_URL}/auth/register/`, {
      username,
      email,
      password
    });
  }

  getCurrentUser() {
    return JSON.parse(localStorage.getItem('user'));
  }

  isAuthenticated() {
    const user = this.getCurrentUser();
    return !!user && !!user.token;
  }

  getToken() {
    const user = this.getCurrentUser();
    return user ? user.token : null;
  }

  encryptData(data) {
    return CryptoJS.AES.encrypt(JSON.stringify(data), process.env.REACT_APP_SECRET_KEY || 'your-secret-key').toString();
  }

  decryptData(encryptedData) {
    const bytes = CryptoJS.AES.decrypt(encryptedData, process.env.REACT_APP_SECRET_KEY || 'your-secret-key');
    return JSON.parse(bytes.toString(CryptoJS.enc.Utf8));
  }

  getAuthHeader() {
    const user = this.getCurrentUser();
    if (user && user.access) {
      return { Authorization: `Bearer ${user.access}` };
    }
    return {};
  }

  async refreshToken() {
    try {
      const user = this.getCurrentUser();
      if (!user || !user.refresh) {
        throw new Error('No refresh token available');
      }

      const response = await axios.post(API_ENDPOINTS.REFRESH_TOKEN, {
        refresh: user.refresh,
      });

      if (response.data.access) {
        const updatedUser = { ...user, access: response.data.access };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        return response.data;
      }
    } catch (error) {
      this.logout();
      throw this.handleError(error);
    }
  }

  handleError(error) {
    if (error.response) {
      // Le serveur a répondu avec un code d'erreur
      return {
        message: error.response.data.detail || 'Une erreur est survenue',
        status: error.response.status,
      };
    } else if (error.request) {
      // La requête a été faite mais aucune réponse n'a été reçue
      return {
        message: 'Impossible de se connecter au serveur',
        status: 0,
      };
    } else {
      // Une erreur s'est produite lors de la configuration de la requête
      return {
        message: error.message || 'Une erreur est survenue',
        status: 0,
      };
    }
  }
}

const authService = new AuthService();
export default authService; 