/* global window, fetch, module */
const BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Notification & Alert Service
 */
class NotificationService {
  constructor() {
    this.notificationsUrl = `${BACKEND_URL}notifications/api/items/`;
    this.markAllReadUrl = `${BACKEND_URL}notifications/mark-all-read/`;
  }

  async getNotifications() {
    try {
      const response = await fetch(this.notificationsUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[NotificationService] Error fetching notifications:", e);
      return [];
    }
  }

  async markAsRead(notificationId) {
    try {
      const response = await fetch(`${this.notificationsUrl}${notificationId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_read: true })
      });
      return { success: response.ok };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async markAllAsRead() {
    try {
      const response = await fetch(this.markAllReadUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      return { success: response.ok };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}

const notificationService = new NotificationService();
if (typeof window !== 'undefined') {
  window.notificationService = notificationService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = notificationService;
}
