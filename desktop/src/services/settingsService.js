/* global window, fetch, module */
const SETTINGS_BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Settings, Profile & Role Service
 */
class SettingsService {
  constructor() {
    this.profileUrl = `${SETTINGS_BACKEND_URL}users/profile/`;
    this.usersUrl = `${SETTINGS_BACKEND_URL}users/api/list/`;
    this.rolesUrl = `${SETTINGS_BACKEND_URL}users/api/roles/`;
    this.changePasswordUrl = `${SETTINGS_BACKEND_URL}users/change-password/`;
  }

  async getUserProfile() {
    try {
      const response = await fetch(this.profileUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      return await response.json();
    } catch (e) {
      console.error("[SettingsService] Error fetching user profile:", e);
      return { username: 'Admin User', role: 'Super Administrator' };
    }
  }

  async getUsersList() {
    try {
      const response = await fetch(this.usersUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[SettingsService] Error fetching users list:", e);
      return [];
    }
  }

  async changePassword(oldPassword, newPassword) {
    try {
      const response = await fetch(this.changePasswordUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
      });
      return { success: response.ok };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}

const settingsService = new SettingsService();
if (typeof window !== 'undefined') {
  window.settingsService = settingsService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = settingsService;
}
