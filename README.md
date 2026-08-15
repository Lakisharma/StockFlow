# 📦 StockFlow AI — Enterprise Warehouse & Inventory Management System

StockFlow AI is a robust, modular, and enterprise-grade Warehouse & Inventory Management System designed to streamline supply chain operations, automate procurement and fulfillment workflows, provide real-time inventory tracking, and deliver business intelligence analytics. Built with a high-performance **Django** backend, modern web UI, and a dedicated **Electron Windows Desktop Application**, StockFlow AI synchronizes operations across web and desktop clients.

---

## 🚀 Key Features & Completed Modules

1. **📦 Product & Inventory Management**: Multi-category product catalog with SKU, barcode generation, batch tracking, unit conversions, reorder thresholds, and live warehouse stock levels.
2. **🏢 Multi-Warehouse & Godown Transfers**: Inter-warehouse transfer workflows with dispatch approval, transit tracking, and receiving inspection.
3. **🛒 Procurement & Supplier Management (PO → GRN)**: Supplier directory, purchase orders, quality checks, goods receipt notes (GRN), and automated stock-in.
4. **🛍️ Sales, Orders & Dispatch (SO → Invoice → Stock-Out)**: Customer database, sales orders, automated picking, dispatch fulfillment, invoice generation, and tax calculation.
5. **💰 Payments & Financial Ledgers**: Customer payments, supplier payments, payment allocations, bank account balances, and automated ledger balancing.
6. **🤖 AI Smart Assistant & OCR Engine**: AI-assisted inventory queries and automated document/invoice barcode scanning.
7. **📊 Analytics & Executive Reports**: Real-time KPI dashboard, sales turnover, inventory valuation, profit margins, and exportable audit reports.
8. **🔒 Security, RBAC & Audit Trails**: Role-based access control (Super Admin, Warehouse Manager, Staff), granular permissions, and tamper-evident audit logs.
9. **🔔 Real-time Notifications**: Alert system for low stock levels, pending approvals, and transaction milestones.
10. **💾 Automated Backups & System Health**: One-click database backups, snapshot restoration, and diagnostic health monitoring.

---

## 🛠️ Technology Stack

- **Web Frontend**: HTML5, Vanilla JavaScript, Vanilla CSS, Material Icons
- **Backend API & Framework**: Python 3.10+, Django 5.x, Django REST Framework
- **Database**: PostgreSQL (Production) / SQLite (Local Development)
- **Desktop Client**: Electron JS, Node.js
- **Deployment & Server**: Gunicorn, Nginx, Render Cloud Platform

---

## ⚙️ Installation & Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Lakisharma/StockFlow.git
cd StockFlow
```

### 2. Set Up Python Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and configure your environment settings:
```bash
cp .env.example .env
```

### 5. Apply Database Migrations & Start Development Server
```bash
python manage.py migrate
python manage.py runserver
```
Access the application locally at `http://127.0.0.1:8000/`.

---

## 🖥️ Desktop Application (Electron)

The StockFlow AI Desktop client connects securely to the centralized production backend API.

### Run Desktop in Development Mode
```bash
cd desktop
npm install
npm run dev
```

### Build Windows Installer
```bash
cd desktop
npm run build:win
```
The compiled Windows installer package will be generated at:
`desktop/dist/StockFlow AI Desktop Setup 1.0.0.exe`

---

## 🌐 Production Configuration

- **Production Backend URL**: Configured via secure environment variables (`BACKEND_URL`).
- **Web App**: Production deployment instructions using Gunicorn and Nginx with SSL are documented in [DEPLOYMENT.md](DEPLOYMENT.md).
- **Cross-Platform Sync**: Both Web and Desktop applications communicate with the shared centralized REST API.

---

## 🛡️ Backup & Disaster Recovery

- Automated database backups and integrity verification are managed under the **Backups** module.
- For backup restoration procedures and disaster recovery runbooks, refer to [BACKUP.md](BACKUP.md) and [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md).

---

## 🔒 Security Best Practices

- Never commit `.env` files, production credentials, or database backups to public version control.
- Ensure `DEBUG=False` and configure strong `SECRET_KEY`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` in production environments.
- Enforce Role-Based Access Control (RBAC) and maintain regular security audits via the System Admin Control Center.

---

## 📄 License
This project is proprietary software for StockFlow AI. All rights reserved.
