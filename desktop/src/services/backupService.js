/* global window, fetch, module */
/**
 * StockFlow AI Desktop Backup, Restore & Data Sync Service
 */
class BackupService {
  constructor() {
    this.recordsUrl = 'http://127.0.0.1:8000/backups/api/records/';
    this.createUrl = 'http://127.0.0.1:8000/backups/create/';
    this.baseUrl = 'http://127.0.0.1:8000/backups/';
  }

  async getBackupHistory() {
    try {
      const response = await fetch(this.recordsUrl);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const data = await response.json();
      return Array.isArray(data) ? data : (data.results || []);
    } catch (e) {
      console.error("[BackupService] Error fetching backup history:", e);
      return [];
    }
  }

  async createManualBackup() {
    try {
      const response = await fetch(this.createUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      return { success: response.ok };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  async restoreBackup(backupId) {
    try {
      const response = await fetch(`${this.baseUrl}${backupId}/restore/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      return { success: response.ok };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}

const backupService = new BackupService();
if (typeof window !== 'undefined') {
  window.backupService = backupService;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = backupService;
}
