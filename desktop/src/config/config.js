/* global window, module */
/**
 * StockFlow AI Desktop Configuration
 * Defines central API endpoints and environment settings.
 */
const CONFIG = {
  API_BASE_URL: 'http://127.0.0.1:8000/api/',
  BACKEND_URL: 'http://127.0.0.1:8000/',
  APP_NAME: 'StockFlow AI Desktop',
  APP_VERSION: '1.0.0'
};

if (typeof window !== 'undefined') {
  window.CONFIG = CONFIG;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CONFIG;
}
