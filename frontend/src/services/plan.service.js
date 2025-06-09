import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';
import authService from './auth.service';

class PlanService {
  async getAllPlans() {
    try {
      const response = await axios.get(API_ENDPOINTS.PLANS, {
        headers: authService.getAuthHeader(),
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getPlanById(planId) {
    try {
      const response = await axios.get(`${API_ENDPOINTS.PLANS}${planId}/`, {
        headers: authService.getAuthHeader(),
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  handleError(error) {
    if (error.response) {
      return {
        message: error.response.data.detail || 'Une erreur est survenue',
        status: error.response.status,
      };
    } else if (error.request) {
      return {
        message: 'Impossible de se connecter au serveur',
        status: 0,
      };
    } else {
      return {
        message: error.message || 'Une erreur est survenue',
        status: 0,
      };
    }
  }
}

export default new PlanService(); 