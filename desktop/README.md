# StockFlow AI — Desktop Application Client

This directory contains the cross-platform **Desktop Application Client** for **StockFlow AI** built with Electron.

---

## 🏗️ Architecture Rule

The desktop application is a **client/interface only**. It connects directly to the existing **Django REST API Backend** and central database (`http://127.0.0.1:8000/api/` or production domain).

```
Desktop App (Electron Client) ───> Django REST API Backend ───> Central PostgreSQL/SQLite DB
```

- **NO Separate Database**: The desktop app does not create a separate business database.
- **NO Duplicate Backend**: All business logic, inventory truth, purchase processing, and permissions remain on the Django server.

---

## 🚀 Running Development Build

```bash
cd desktop
npm install
npm run dev
```

---

## 📦 Building Windows (.exe) Installer

```bash
cd desktop
npm run dist
```
Generates Windows `.exe` installer and portable packages in `desktop/dist/`.
