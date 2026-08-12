/* global window, fetch, module */
/**
 * StockFlow AI Central API Service
 */
class ApiService {
  constructor() {
    this.baseUrl = 'http://127.0.0.1:8000/api/';
    this.healthUrl = 'http://127.0.0.1:8000/health/';
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
