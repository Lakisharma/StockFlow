/* global window, module */
/**
 * StockFlow AI Desktop Configuration
 * Defines central API endpoints and environment settings.
 */
const isDev = typeof window !== 'undefined' && window.electronAPI && typeof window.electronAPI.getEnv === 'function' && window.electronAPI.getEnv() === 'development';
const BACKEND_URL = isDev ? 'http://127.0.0.1:8000/' : 'https://stockflow-xixv.onrender.com/';

const CONFIG = {
  API_BASE_URL: `${BACKEND_URL}api/`,
  BACKEND_URL: BACKEND_URL,
  APP_NAME: 'StockFlow AI Desktop',
  APP_VERSION: '1.0.0',
  ENV: isDev ? 'development' : 'production'
};

if (typeof window !== 'undefined') {
  window.CONFIG = CONFIG;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CONFIG;
}
