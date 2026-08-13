/* global window, fetch, module */
const BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Natural Language Assistant Service
 */
class AiAssistantService {
  constructor() {
    this.searchUrl = `${BACKEND_URL}api/search/`;
    this.queryUrl = `${BACKEND_URL}api/ai/query/`;
  }

  async parseAndExecuteQuery(queryText) {
    const q = queryText.toLowerCase().trim();

    try {
      if (q.includes("sales") || q.includes("biki") || q.includes("revenue")) {
        const res = await fetch(`${BACKEND_URL}reports/api/metrics/`);
        const data = await res.json();
        return {
          type: 'info',
          response_text: `Today's Sales Revenue is $${parseFloat(data.total_sales || 0).toFixed(2)}.`,
          data
        };
      }

      if (q.includes("low stock") || q.includes("kam stock")) {
        const res = await fetch(`${BACKEND_URL}products/api/stock/`);
        const data = await res.json();
        const items = Array.isArray(data) ? data : (data.results || []);
        const lowItems = items.filter(i => i.quantity <= 10);
        return {
          type: 'info',
          response_text: `Found ${lowItems.length} low stock items.`,
          data: lowItems
        };
      }

      const res = await fetch(`${this.searchUrl}?q=${encodeURIComponent(queryText)}`);
      const searchData = await res.json();
      return {
        type: 'search',
        response_text: `Search results for "${queryText}":`,
        data: searchData
      };
    } catch (e) {
      console.error("[AiAssistantService] Query Error:", e);
      return { type: 'error', response_text: "Failed to process query with AI backend." };
    }
  }
}

const aiAssistantService = new AiAssistantService();
if (typeof window !== 'undefined') {
  window.aiAssistantService = aiAssistantService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = aiAssistantService;
}
