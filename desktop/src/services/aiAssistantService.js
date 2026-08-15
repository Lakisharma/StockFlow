/* global window, fetch, module */
const AI_ASSISTANT_BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Natural Language Assistant Service
 */
class AiAssistantService {
  constructor() {
    this.searchUrl = `${AI_ASSISTANT_BACKEND_URL}api/search/`;
    this.queryUrl = `${AI_ASSISTANT_BACKEND_URL}api/ai/query/`;
  }

  async parseAndExecuteQuery(queryText) {
    const q = (queryText || '').toLowerCase().trim();
    if (!q) return { type: 'info', response_text: "Please type a question or select a quick topic below." };

    try {
      // 1. Sales & Revenue queries
      if (q.includes("sales") || q.includes("biki") || q.includes("bikri") || q.includes("revenue") || q.includes("turnover") || q.includes("income")) {
        const res = await fetch(`${AI_ASSISTANT_BACKEND_URL}reports/api/metrics/`);
        const data = await res.json().catch(() => ({}));
        const totalSales = parseFloat(data.total_sales || 0).toFixed(2);
        return {
          type: 'sales',
          response_text: `📊 **Sales Summary:**\n• Total Sales Revenue: ₹${totalSales}\n• Active Invoices: ${data.total_sales_count || 0}\n• All transactions are synced with the central ERP database.`,
          data
        };
      }

      // 2. Low Stock & Reorder queries
      if (q.includes("low stock") || q.includes("kam stock") || q.includes("shortage") || q.includes("reorder")) {
        const res = await fetch(`${AI_ASSISTANT_BACKEND_URL}products/api/products/`);
        const data = await res.json().catch(() => []);
        const items = Array.isArray(data) ? data : (data.results || []);
        const lowItems = items.filter(i => (i.current_stock || 0) <= (i.min_stock_level || 10));
        
        if (lowItems.length === 0) {
          return {
            type: 'stock',
            response_text: `✅ **Stock Health Good!** No products are currently below reorder threshold. Total active SKUs: ${items.length}.`,
            data: []
          };
        }

        const itemsList = lowItems.map(i => `• **${i.name}** (SKU: \`${i.sku}\`) — Stock: **${i.current_stock}** (Min: ${i.min_stock_level || 5})`).join('\n');
        return {
          type: 'stock',
          response_text: `⚠️ **Low Stock Alert (${lowItems.length} items):**\n${itemsList}\n\nPlease generate a Purchase Order to restock these items.`,
          data: lowItems
        };
      }

      // 3. Products Catalog & Stock Queries
      if (q.includes("product") || q.includes("products") || q.includes("item") || q.includes("catalog") || q.includes("kya hai") || q.includes("stock") || q.includes("maal") || q.includes("list")) {
        const res = await fetch(`${AI_ASSISTANT_BACKEND_URL}products/api/products/`);
        const data = await res.json().catch(() => []);
        const items = Array.isArray(data) ? data : (data.results || []);
        
        if (items.length === 0) {
          return {
            type: 'products',
            response_text: `📦 **Products Catalog:** No products registered yet. Click **"Add New Product"** in Products & Catalog to create your first SKU.`,
            data: []
          };
        }

        const itemsList = items.map(i => `• **${i.name}** | SKU: \`${i.sku}\` | Price: **₹${i.selling_price}** | Available Stock: **${i.current_stock}**`).join('\n');
        return {
          type: 'products',
          response_text: `📦 **Live Product Catalog (${items.length} SKUs):**\n${itemsList}`,
          data: items
        };
      }

      // 4. Purchases & Procurement queries
      if (q.includes("purchase") || q.includes("kharid") || q.includes("khareed") || q.includes("procurement") || q.includes("po")) {
        const res = await fetch(`${AI_ASSISTANT_BACKEND_URL}reports/api/metrics/`);
        const data = await res.json().catch(() => ({}));
        const totalPurchases = parseFloat(data.total_purchase_amount || data.total_purchases || 0).toFixed(2);
        return {
          type: 'purchases',
          response_text: `🛍️ **Procurement Summary:**\n• Total Purchases: ₹${totalPurchases}\n• Total Purchase Orders: ${data.total_purchases_count || data.total_purchases || 0}\n• Check Purchase Orders tab to view Goods Receipt Notes (GRN).`,
          data
        };
      }

      // 5. Suppliers / Vendors queries
      if (q.includes("supplier") || q.includes("vendor") || q.includes("dealer")) {
        const res = await fetch(`${AI_ASSISTANT_BACKEND_URL}suppliers/api/suppliers/`);
        const data = await res.json().catch(() => []);
        const suppliers = Array.isArray(data) ? data : (data.results || []);
        if (suppliers.length === 0) {
          return {
            type: 'suppliers',
            response_text: `🚚 **Suppliers:** No suppliers registered yet. You can register suppliers via the Suppliers module.`,
            data: []
          };
        }
        const sList = suppliers.map(s => `• **${s.name || s.company_name}** | Code: \`${s.code}\` | Phone: ${s.phone || '--'}`).join('\n');
        return {
          type: 'suppliers',
          response_text: `🚚 **Active Suppliers (${suppliers.length}):**\n${sList}`,
          data: suppliers
        };
      }

      // 6. Expense creation helper
      if (q.includes("expense") || q.includes("kharcha")) {
        return {
          type: 'expense',
          response_text: `💸 **Expense Logging:** You can log expenses directly in the **Accounting & Expenses** tab or tell me details like *"Create expense of ₹500 for transport"* to record operating expenses.`,
          data: null
        };
      }

      // Default Intelligent ERP Response
      return {
        type: 'general',
        response_text: `🤖 **StockFlow AI Assistant:** I am monitoring your live warehouse and inventory operations. You can ask me:\n• *"Show all products and stock"*\n• *"Which items are low in stock?"*\n• *"What is today's sales revenue?"*\n• *"Show registered suppliers"*`,
        data: null
      };
    } catch (e) {
      console.error("[AiAssistantService] Query Error:", e);
      return { type: 'error', response_text: "⚠️ Could not connect to AI service. Please check your internet connection." };
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
