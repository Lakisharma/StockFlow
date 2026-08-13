/* global window, fetch, module */
const BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Sales Dispatches & Invoicing Service
 */
class SalesService {
  constructor() {
    this.ordersUrl = `${BACKEND_URL}sales/api/orders/`;
    this.customersUrl = `${BACKEND_URL}sales/api/customers/`;
  }

  async getSalesDispatches() {
    try {
      const response = await fetch(this.ordersUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[SalesService] Error fetching sales dispatches:", e);
      return [];
    }
  }

  async getCustomers() {
    try {
      const response = await fetch(this.customersUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[SalesService] Error fetching customers:", e);
      return [];
    }
  }
}

const salesService = new SalesService();
if (typeof window !== 'undefined') {
  window.salesService = salesService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = salesService;
}
