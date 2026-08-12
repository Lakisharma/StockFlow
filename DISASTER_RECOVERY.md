# StockFlow AI — Disaster Recovery & Business Continuity Plan

This document outlines the emergency recovery procedures, RTO/RPO targets, database restoration steps, and integrity verification protocols for **StockFlow AI**.

---

## 🎯 1. Target Recovery Metrics (RTO & RPO)

| Metric | Target | Description |
|--------|--------|-------------|
| **RTO (Recovery Time Objective)** | **< 30 Minutes** | Maximum acceptable downtime to restore full system operations following a major outage. |
| **RPO (Recovery Point Objective)** | **< 24 Hours** | Maximum acceptable data loss window (backed up daily at 02:00 AM or immediately via pre-restore safety backups). |

---

## 🚨 2. Disaster Scenarios & Recovery Procedures

### Scenario A: Database Corruption or Accidental Record Deletion
1. Log in as Administrator and navigate to **Backup & Restore** (`/backups/`).
2. Select the latest **Verified** backup record (`verification_status: 'verified'`).
3. Click **Restore System Data**.
4. Confirm restoration. The system automatically creates a **Safety Backup** (`before_restore`) of the current state before executing restoration.
5. Verify database integrity at `/health/` or by running `DatabaseIntegrityService.run_integrity_check()`.

### Scenario B: Complete Server / Virtual Machine Failure
1. Provision a new server instance (Ubuntu 22.04 LTS / Debian 12).
2. Clone repository and install dependencies (`pip install -r requirements.txt`).
3. Configure environment variables in `.env` matching production parameters.
4. Copy the latest `.zip` backup archive into `media/backups/`.
5. Execute restoration via Django management command or python script:
   ```python
   from backups.models import BackupRecord
   from backups.services import BackupEngineService

   record = BackupRecord.objects.get(backup_id='BKUP-YYYYMMDD-HHMMSS-XXXX')
   BackupEngineService.restore_backup(record)
   ```
6. Start Gunicorn WSGI server and Nginx proxy (`systemctl restart stockflow nginx`).

---

## ⚖️ 3. Database Integrity & Data Reconciliation

After restoring a database backup, execute the automated Database Integrity Check:

```python
from backups.services import DatabaseIntegrityService
report = DatabaseIntegrityService.run_integrity_check()
print(report)
```

The check inspects:
- **Inventory Balances**: Verifies no negative stock items exist.
- **Accounting Ledger**: Verifies Debit equals Credit for all financial journal entries.
- **Batches & Serials**: Verifies all batch numbers and serials map to valid product IDs.

---

## 📝 4. Audit Log Trail

All disaster recovery operations (backup creation, restore initialization, safety backups, integrity checks, and retention cleanups) are recorded in the **Central Audit Log** (`audit_logs/`) for security compliance.
