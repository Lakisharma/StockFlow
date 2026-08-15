/* global window, fetch, module */
const PRODUCT_BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Product Catalog Service
 */
class ProductService {
  constructor() {
    this.productsUrl = `${PRODUCT_BACKEND_URL}products/api/products/`;
  }

  async getProducts() {
    try {
      const response = await fetch(this.productsUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[ProductService] Error fetching products:", e);
      return [];
    }
  }

  async createProduct(productData) {
    try {
      const token = (typeof localStorage !== 'undefined' && localStorage.getItem('sf_user_token')) || '';
      
      let categoryId = null;
      let unitId = null;

      try {
        const catRes = await fetch(`${PRODUCT_BACKEND_URL}categories/api/`);
        if (catRes.ok) {
          const catData = await catRes.json();
          const cats = Array.isArray(catData) ? catData : (catData.results || []);
          if (cats.length > 0) categoryId = cats[0].id;
        }
      } catch (e) {
        console.warn("Could not fetch categories:", e);
      }

      try {
        const unitRes = await fetch(`${PRODUCT_BACKEND_URL}units/api/`);
        if (unitRes.ok) {
          const unitData = await unitRes.json();
          const units = Array.isArray(unitData) ? unitData : (unitData.results || []);
          if (units.length > 0) unitId = units[0].id;
        }
      } catch (e) {
        console.warn("Could not fetch units:", e);
      }

      const payload = {
        name: productData.name,
        sku: productData.sku,
        barcode: productData.barcode || '',
        purchase_price: productData.purchase_price || (parseFloat(productData.selling_price || 0) * 0.7).toFixed(2),
        selling_price: productData.selling_price || '0.00',
        mrp: productData.mrp || productData.selling_price || '0.00',
        gst_rate: productData.gst_rate || '18.00',
        current_stock: parseInt(productData.current_stock || productData.reorder_level || 0, 10),
        min_stock_level: parseInt(productData.reorder_level || 5, 10),
        status: 'active'
      };

      if (categoryId) payload.category = categoryId;
      if (unitId) payload.unit = unitId;

      const response = await fetch(this.productsUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`
        },
        body: JSON.stringify(payload)
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const errMsg = typeof data === 'object' ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ') : 'Failed to create product';
        return { success: false, error: errMsg };
      }
      return { success: true, data };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}

const productService = new ProductService();
if (typeof window !== 'undefined') {
  window.productService = productService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = productService;
}
