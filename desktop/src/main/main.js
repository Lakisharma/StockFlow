/* global __dirname, process, require */
/**
 * StockFlow AI Desktop Main Process
 * Manages Electron application lifecycle, window controls, and IPC security bridges.
 */
const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');

let mainWindow = null;

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'StockFlow AI Desktop',
    frame: false, // Custom Window Titlebar Frame
    backgroundColor: '#0f172a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true
    }
  });

  // Remove default menu bar for custom enterprise desktop look
  Menu.setApplicationMenu(null);

  // Load Desktop Renderer Interface
  const rendererPath = path.join(__dirname, '../renderer/index.html');
  mainWindow.loadFile(rendererPath);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Window Management IPC Handlers
ipcMain.on('window-minimize', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.on('window-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.on('window-close', () => {
  if (mainWindow) mainWindow.close();
});

ipcMain.on('network-status-changed', (event, isOnline) => {
  console.log(`[Desktop Main] System Connectivity Status: ${isOnline ? 'Online' : 'Offline'}`);
});

ipcMain.on('get-env', (event) => {
  event.returnValue = process.argv.includes('--env=development') ? 'development' : 'production';
});

// Application Lifecycle Event Listeners
app.whenReady().then(() => {
  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
