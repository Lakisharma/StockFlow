/* global window, fetch, module */
/**
 * StockFlow AI Sales Dispatches & Invoicing Service
 */
class SalesService {
  constructor() {
    this.ordersUrl = 'http://127.0.0.1:8000/sales/api/orders/';
    this.customersUrl = 'http://127.0.0.1:8000/sales/api/customers/';
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
