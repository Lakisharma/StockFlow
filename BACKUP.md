# StockFlow AI — Production Backup & Retention Architecture Guide

This document specifies the backup, archival, retention, and verification policies for the **StockFlow AI** Enterprise Warehouse & Inventory Management System.

---

## 📦 1. Backup Architecture Overview

StockFlow AI uses a unified multi-app serialization engine (`BackupEngineService`) that captures:
1. **Database Content**: Complete JSON relational dump of all 25+ business modules (Users, Roles, Permissions, Products, Categories, Brands, Units, Suppliers, Customers, Warehouses, Inventory, Batches, Serials, Purchases, Sales, Dispatches, Payments, Accounting, Employees, Attendance, Notifications, Audit Logs, Settings).
2. **Media Assets**: Complete archive of all uploaded product images, company logos, OCR invoice bills, and PDF documents stored under `media/`.
3. **Integrity Validation**: Computes a 256-bit SHA256 cryptographic checksum and verifies archive readability using `zipfile.testzip()`.

---

## ⏱️ 2. Backup Schedules & Frequency

Backup frequency can be configured by administrators via the Admin Dashboard (`/backups/settings/`):

- **Daily Backups**: Automatically generated at 02:00 AM server time.
- **Pre-Update Safety Backups**: Automatically generated prior to database migrations or system updates.
- **Pre-Restore Safety Backups**: Automatically generated before executing any database restoration.
- **Manual Backups**: Triggered on-demand by authorized Administrators via the UI (`/backups/create/`).

---

## 🔒 3. Backup Retention Policy

To prevent storage exhaustion while preserving critical historical data, StockFlow AI enforces configurable retention rules:

- **Keep Last 5 Backups**
- **Keep Last 10 Backups** (Default)
- **Keep Last 30 Backups**
- **Custom Retention Count**

When a new backup completes, older backups exceeding the configured retention threshold are automatically deleted from local storage, creating an audit log entry (`RBACService.log_activity`).

---

## 🛡️ 4. Backup Security & RBAC Access Control

- **Role-Based Access Control**: Only Superusers and Administrators assigned explicit `can_manage_backups` permissions can create, view, restore, or delete backups.
- **No Public Access**: Backup files are stored securely inside the server filesystem (`media/backups/`) and are non-browsable publicly.
- **SHA256 Checksum**: Ensures backup archives are tamper-evident.
