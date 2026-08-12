# StockFlow AI — Desktop Application Architecture & Setup Manual

This document details the architecture, setup instructions, security parameters, and packaging procedures for the **StockFlow AI Desktop Client** located in `/desktop/`.

---

## 🏛️ 1. Single Source of Truth Architecture

```
                  ┌────────────────────────┐
                  │    StockFlow AI        │
                  │   Django REST API      │
                  │   (Central Server)     │
                  └───────────┬────────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
    ┌────────┴────────┐ ┌─────┴──────┐ ┌───────┴────────┐
    │  Web Browser    │ │ Desktop    │ │ Mobile App     │
    │  Interface      │ │ Client     │ │ (Future)       │
    └─────────────────┘ └────────────┘ └────────────────┘
```

> [!IMPORTANT]
> The desktop application does NOT contain a separate database or business backend logic. It interfaces directly with the Django backend REST endpoints. User authentication and Role-Based Access Control (RBAC) are evaluated directly against the backend server.

---

## 📂 2. Desktop Directory Structure

```
/desktop
  ├── package.json                   # Electron & Build scripts
  ├── electron-builder.json          # Windows NSIS Installer configuration
  ├── README.md                      # Quickstart guide
  └── /src
      ├── /config
      │   └── config.js              # Centralized API Base URL & settings
      ├── /main
      │   ├── main.js                # Electron Main process lifecycle
      │   └── preload.js             # Secure IPC bridge (window.electronAPI)
      ├── /services
      │   ├── apiService.js          # Reusable HTTP client for Django API
      │   └── authService.js         # Desktop login & session manager
      └── /renderer
          ├── index.html             # Desktop UI layout & module views
          ├── styles.css             # Enterprise dark-slate design system
          └── app.js                 # Renderer logic & barcode scanner handler
```

---

## 🔒 3. Security & Context Isolation

The desktop client implements Electron security best practices:
- **`contextIsolation: true`**: Prevents web pages from accessing Node.js runtime internals.
- **`nodeIntegration: false`**: Blocks direct Node.js code execution in the renderer thread.
- **`sandbox: true`**: Runs renderer processes in an isolated OS sandbox.
- **Secure Preload Bridge**: Exposes safe window control functions (`minimize`, `maximize`, `close`) via `window.electronAPI`.

---

## 🔌 4. API & Hardware Integration

1. **Central API Server**: Connects to `http://127.0.0.1:8000/api/` (Development) or `https://production-domain/api/` (Production).
2. **USB Barcode Scanner**: Listens for hardware keyboard scanner events and automatically queries the Django global search API (`/api/search/?q=BARCODE`).
3. **Offline Detection**: Automatically monitors network connectivity status and alerts the user if server connection drops.

---

## 🛠️ 5. Windows (.exe) Installer Build Steps

### Prerequisites
- Node.js v18+ & `npm`

### Step-by-Step Commands
```bash
# 1. Navigate to desktop directory
cd desktop

# 2. Install dependencies
npm install

# 3. Launch Development Desktop Client
npm run dev

# 4. Generate Production Windows NSIS (.exe) Installer
npm run dist
```

Output installers are generated under `desktop/dist/`:
- `StockFlow AI Desktop Setup 1.0.0.exe` (NSIS Installer)
- `StockFlow AI Desktop 1.0.0.exe` (Portable Version)
