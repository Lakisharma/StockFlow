/* global window, fetch, module */
const BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Stock Transfer Service
 */
class TransferService {
  constructor() {
    this.transfersUrl = `${BACKEND_URL}transfers/api/transfers/`;
  }

  async getStockTransfers() {
    try {
      const response = await fetch(this.transfersUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[TransferService] Error fetching stock transfers:", e);
      return [];
    }
  }

  async createStockTransfer(transferData) {
    try {
      const response = await fetch(this.transfersUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(transferData)
      });
      return { success: response.ok, data: await response.json() };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}

const transferService = new TransferService();
if (typeof window !== 'undefined') {
  window.transferService = transferService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = transferService;
}
