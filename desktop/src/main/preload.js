/* global require */
/**
 * StockFlow AI Desktop Preload Script
 * Secure IPC bridge between Electron Main Process and Desktop Renderer UI.
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Window Management APIs
  minimizeWindow: () => ipcRenderer.send('window-minimize'),
  maximizeWindow: () => ipcRenderer.send('window-maximize'),
  closeWindow: () => ipcRenderer.send('window-close'),

  // Environment & Version Info
  getAppVersion: () => '1.0.0',
  isDesktop: true,

  // USB Barcode Scanner Listener Bridge
  onScannerInput: (callback) => {
    ipcRenderer.on('usb-barcode-scanned', (event, barcode) => callback(barcode));
  },

  // Network Status Notification Bridge
  sendNetworkStatus: (isOnline) => ipcRenderer.send('network-status-changed', isOnline)
});
