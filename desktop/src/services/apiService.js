/* global window, fetch, module */
const API_SERVICE_BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Central API Service
 */
class ApiService {
  constructor() {
    this.baseUrl = typeof CONFIG !== 'undefined' ? CONFIG.API_BASE_URL : `${API_SERVICE_BACKEND_URL}api/`;
    this.healthUrl = `${API_SERVICE_BACKEND_URL}health/`;
  }

  async checkHealth() {
    try {
      const response = await fetch(this.healthUrl);
      return response.ok;
    } catch (e) {
      console.warn("[ApiService] Health check failed:", e);
      return false;
    }
  }

  async get(endpoint) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      return await response.json();
    } catch (e) {
      console.error(`[ApiService] GET ${endpoint} error:`, e);
      throw e;
    }
  }
}

const apiService = new ApiService();
if (typeof window !== 'undefined') {
  window.apiService = apiService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = apiService;
}
