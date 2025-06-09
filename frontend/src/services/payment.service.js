import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';
import authService from './auth.service';
import CryptoJS from 'crypto-js';

class PaymentService {
  // Clé de chiffrement (à stocker dans les variables d'environnement en production)
  static ENCRYPTION_KEY = 'bestconnect-secure-key-2024';

  // Fonction pour crypter le numéro de transaction
  static encryptTransactionNumber(number) {
    try {
      // Suppression des espaces et caractères spéciaux
      const cleanNumber = number.replace(/\D/g, '');
      
      // Cryptage avec AES
      const encrypted = CryptoJS.AES.encrypt(
        cleanNumber,
        this.ENCRYPTION_KEY
      ).toString();

      // Encodage en base64 pour une meilleure compatibilité
      return btoa(encrypted);
    } catch (error) {
      console.error('Erreur de cryptage:', error);
      throw new Error('Erreur lors du cryptage du numéro de transaction');
    }
  }

  // Fonction pour décrypter le numéro de transaction
  static decryptTransactionNumber(encryptedNumber) {
    try {
      // Décodage du base64
      const decoded = atob(encryptedNumber);
      
      // Décryptage avec AES
      const decrypted = CryptoJS.AES.decrypt(
        decoded,
        this.ENCRYPTION_KEY
      ).toString(CryptoJS.enc.Utf8);

      return decrypted;
    } catch (error) {
      console.error('Erreur de décryptage:', error);
      throw new Error('Erreur lors du décryptage du numéro de transaction');
    }
  }

  async createPayment(planId, paymentData) {
    try {
      // Cryptage du numéro de transaction
      const encryptedTransactionNumber = PaymentService.encryptTransactionNumber('034 72 497 15');

      const response = await axios.post(
        API_ENDPOINTS.PAYMENTS,
        {
          plan: planId,
          ...paymentData,
          transaction_number: encryptedTransactionNumber,
          transaction_number_hash: CryptoJS.SHA256(encryptedTransactionNumber).toString(), // Hash pour vérification
        },
        {
          headers: authService.getAuthHeader(),
        }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getPaymentStatus(paymentId) {
    try {
      const response = await axios.get(
        `${API_ENDPOINTS.PAYMENTS}${paymentId}/status/`,
        {
          headers: authService.getAuthHeader(),
        }
      );
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

export default new PaymentService(); 