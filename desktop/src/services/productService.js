/* global window, fetch, module */
const BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Product Catalog Service
 */
class ProductService {
  constructor() {
    this.productsUrl = `${BACKEND_URL}products/api/products/`;
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
      const response = await fetch(this.productsUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(productData)
      });
      return { success: response.ok, data: await response.json() };
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
