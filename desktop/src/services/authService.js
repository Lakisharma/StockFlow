/* global window, fetch, localStorage, module */
const AUTH_BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Authentication Service
 */
class AuthService {
  constructor() {
    this.loginUrl = `${AUTH_BACKEND_URL}users/login/`;
  }

  async login(username, password) {
    try {
      const response = await fetch(this.loginUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.success) {
        return { success: false, error: data.error || "Invalid username/email or password" };
      }
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('sf_user_token', data.token || 'demo_token');
        localStorage.setItem('sf_user_name', username);
      }
      return { success: true, data };
    } catch (e) {
      return { success: false, error: e.message || `Connection failed to ${typeof CONFIG !== "undefined" ? CONFIG.API_BASE_URL : "http://127.0.0.1:8000/api/"}` };
    }
  }

  logout() {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('sf_user_token');
      localStorage.removeItem('sf_user_name');
    }
  }

  isAuthenticated() {
    return typeof localStorage !== 'undefined' && !!localStorage.getItem('sf_user_token');
  }
}

const authService = new AuthService();
if (typeof window !== 'undefined') {
  window.authService = authService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = authService;
}
