/* global window, fetch, module */
/**
 * StockFlow AI Inventory & Stock Balances Service
 */
class InventoryService {
  constructor() {
    this.stockUrl = 'http://127.0.0.1:8000/products/api/stocks/';
    this.warehousesUrl = 'http://127.0.0.1:8000/products/api/warehouses/';
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
