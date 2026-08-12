/* global window, fetch, localStorage, module */
/**
 * StockFlow AI Authentication Service
 */
class AuthService {
  constructor() {
    this.loginUrl = 'http://127.0.0.1:8000/users/login/';
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
      return { success: false, error: e.message || "Connection failed to http://127.0.0.1:8000/api/" };
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
