/* global window, fetch, module */
const REPORT_BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Reports & Executive Analytics Service
 */
class ReportService {
  constructor() {
    this.metricsUrl = `${REPORT_BACKEND_URL}reports/api/metrics/`;
    this.comparisonUrl = `${REPORT_BACKEND_URL}reports/api/comparison/`;
  }

  async getDashboardMetrics() {
    try {
      const response = await fetch(this.metricsUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      return await response.json();
    } catch (e) {
      console.error("[ReportService] Error fetching report metrics:", e);
      return { total_sales: 0, total_purchases: 0, inventory_value: 0, low_stock_count: 0 };
    }
  }

  async getWarehouseComparison() {
    try {
      const response = await fetch(this.comparisonUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[ReportService] Error fetching warehouse comparison:", e);
      return [];
    }
  }
}

const reportService = new ReportService();
if (typeof window !== 'undefined') {
  window.reportService = reportService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = reportService;
}
