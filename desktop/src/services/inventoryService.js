/* global window, fetch, module */
const BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Inventory & Stock Balances Service
 */
class InventoryService {
  constructor() {
    this.stockUrl = `${BACKEND_URL}products/api/stocks/`;
    this.warehousesUrl = `${BACKEND_URL}products/api/warehouses/`;
  }

  async getWarehouseStock() {
    try {
      const response = await fetch(this.stockUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[InventoryService] Error fetching warehouse stock:", e);
      return [];
    }
  }

  async getWarehouses() {
    try {
      const response = await fetch(this.warehousesUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[InventoryService] Error fetching warehouses:", e);
      return [];
    }
  }
}

const inventoryService = new InventoryService();
if (typeof window !== 'undefined') {
  window.inventoryService = inventoryService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = inventoryService;
}
