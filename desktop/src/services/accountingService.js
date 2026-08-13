/* global window, fetch, module */
const ACCOUNTING_BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Accounting & Expenses Service
 */
class AccountingService {
  constructor() {
    this.expensesUrl = `${ACCOUNTING_BACKEND_URL}accounting/api/expenses/`;
    this.vouchersUrl = `${ACCOUNTING_BACKEND_URL}accounting/api/vouchers/`;
  }

  async getExpenses() {
    try {
      const response = await fetch(this.expensesUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[AccountingService] Error fetching expenses:", e);
      return [];
    }
  }

  async getPaymentVouchers() {
    try {
      const response = await fetch(this.vouchersUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[AccountingService] Error fetching payment vouchers:", e);
      return [];
    }
  }
}

const accountingService = new AccountingService();
if (typeof window !== 'undefined') {
  window.accountingService = accountingService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = accountingService;
}
