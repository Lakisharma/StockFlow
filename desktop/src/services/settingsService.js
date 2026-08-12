/* global window, fetch, module */
/**
 * StockFlow AI Settings, Profile & Role Service
 */
class SettingsService {
  constructor() {
    this.profileUrl = 'http://127.0.0.1:8000/users/profile/';
    this.usersUrl = 'http://127.0.0.1:8000/users/api/list/';
    this.rolesUrl = 'http://127.0.0.1:8000/users/api/roles/';
    this.changePasswordUrl = 'http://127.0.0.1:8000/users/change-password/';
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
