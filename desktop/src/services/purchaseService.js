/* global window, fetch, module */
const BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Purchase Orders & GRN Service
 */
class PurchaseService {
  constructor() {
    this.ordersUrl = `${BACKEND_URL}purchases/api/orders/`;
    this.suppliersUrl = `${BACKEND_URL}purchases/api/suppliers/`;
  }

  async getPurchaseOrders() {
    try {
      const response = await fetch(this.ordersUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[PurchaseService] Error fetching purchase orders:", e);
      return [];
    }
  }

  async getSuppliers() {
    try {
      const response = await fetch(this.suppliersUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[PurchaseService] Error fetching suppliers:", e);
      return [];
    }
  }
}

const purchaseService = new PurchaseService();
if (typeof window !== 'undefined') {
  window.purchaseService = purchaseService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = purchaseService;
}
