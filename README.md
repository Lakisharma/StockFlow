# 📦 StockFlow AI — Enterprise Warehouse & Inventory Management System

StockFlow AI is a robust, modular, and enterprise-grade Warehouse & Inventory Management System designed to streamline business operations, automate workflows, and provide deep analytics. Built using **Django** and **Vanilla Javascript/CSS**, it provides a high-performance solution for inventory tracking, sales/purchase management, multi-warehouse transfers, audit logs, OCR scanning, and desktop application integration.

---

## 🚀 Key Modules & Features

StockFlow AI is structured into highly cohesive modules, each managing a specific domain of warehouse operations:

1. **📦 Inventory & Products**: Comprehensive product catalog with variants, batches, units, and brand tracking.
2. **🏢 Multi-Warehouse Transfers**: Seamless movement of stock between different locations with status tracking.
3. **📊 Sales & Purchases**: Manage purchase orders from suppliers and sales invoices for customers.
4. **🔍 OCR Scanner**: Automated barcode and document scanning using OCR technology to speed up data entry.
5. **💰 Accounting & Payments**: In-built accounting ledgers, invoices, payment tracking, and financial reconciliation.
6. **📈 Analytics & Reports**: Visual reports, sales forecasting, inventory levels, and business health metrics.
7. **🔒 System Admin & Audit Logs**: High-security audit trail tracking user activities, changes, and system events.
8. **👥 User & Employee Management**: Role-Based Access Control (RBAC) for administrators, managers, and warehouse staff.
9. **🔔 Real-time Notifications**: Alerts for low stock levels, pending transfers, and system updates.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+ & Django
- **Frontend**: Vanilla JS, Vanilla CSS, HTML5
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Scanning**: OCR scanning engine
- **WSGI/Proxy**: Gunicorn & Nginx (for Linux deployment)

---

## ⚙️ Quick Start (Local Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/Lakisharma/StockFlow.git
cd StockFlow
```

### 2. Set Up a Virtual Environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Copy `.env.example` to `.env` and adjust the variables:
```bash
cp .env.example .env
```

### 5. Apply Migrations & Start Server
```bash
python manage.py migrate
python manage.py runserver
```
Visit the local instance at `http://127.0.0.1:8000/`.

---

## 🌐 Production Deployment

Refer to the complete deployment guide in [DEPLOYMENT.md](DEPLOYMENT.md) for Nginx, Gunicorn, SSL installation, and database configurations.

## 🛡️ Backup & Disaster Recovery

Refer to [BACKUP.md](BACKUP.md) and [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md) for database backup automation scripts, recovery manuals, and system maintenance instructions.
