/* global window, fetch, module */
const BACKUP_BACKEND_URL = typeof CONFIG !== 'undefined' ? CONFIG.BACKEND_URL : 'http://127.0.0.1:8000/';

/**
 * StockFlow AI Desktop Backup, Restore & Data Sync Service
 */
class BackupService {
  constructor() {
    this.recordsUrl = `${BACKUP_BACKEND_URL}backups/api/records/`;
    this.createUrl = `${BACKUP_BACKEND_URL}backups/create/`;
    this.baseUrl = `${BACKUP_BACKEND_URL}backups/`;
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
