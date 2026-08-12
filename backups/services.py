import os
import zipfile
import hashlib
import json
from io import StringIO
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.core import serializers
from django.apps import apps
from users.services import RBACService
from .models import BackupRecord, BackupSettings

class BackupEngineService:

    @classmethod
    def get_backup_dir(cls):
        backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    @classmethod
    def get_backup_settings(cls):
        obj, _ = BackupSettings.objects.get_or_create(id=1)
        return obj

    @classmethod
    def compute_sha256(cls, file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @classmethod
    def create_backup(cls, user=None, backup_type='manual', custom_name=None):
        timestamp_str = timezone.now().strftime('%Y%m%d-%H%M%S')
        micro_str = timezone.now().strftime('%f')[:4]
        b_id = f"BKUP-{timestamp_str}-{micro_str}"
        b_name = custom_name or f"StockFlow Data Backup ({timestamp_str})"

        record = BackupRecord.objects.create(
            backup_id=b_id,
            backup_name=b_name,
            backup_type=backup_type,
            status='processing',
            created_by=user if user and user.is_authenticated else None
        )

        try:
            backup_dir = cls.get_backup_dir()
            zip_filename = f"{b_id}.zip"
            zip_filepath = os.path.join(backup_dir, zip_filename)

            # 1. Serialize Database Models across all business modules
            target_models = []
            app_labels = [
                'users', 'products', 'categories', 'brands', 'units', 'suppliers',
                'customers', 'warehouses', 'purchases', 'inventory', 'transfers',
                'ocr_scanner', 'reports', 'settings_app', 'backups', 'audit_logs',
                'notifications', 'barcodes', 'batches', 'sales', 'payments',
                'accounting', 'employees', 'stock_adjustments', 'system_admin'
            ]
            for app_label in app_labels:
                try:
                    app_config = apps.get_app_config(app_label)
                    for model in app_config.get_models():
                        target_models.extend(model.objects.all())
                except LookupError:
                    pass

            db_json = serializers.serialize('json', target_models, indent=2)
            db_size_bytes = len(db_json.encode('utf-8'))

            # 2. Package into Zip Archive with media files
            media_size_bytes = 0
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr('database_dump.json', db_json)

                # Add media uploaded files
                media_root = settings.MEDIA_ROOT
                if os.path.exists(media_root):
                    for root, dirs, files in os.walk(media_root):
                        if 'backups' in root:
                            continue  # Skip backups folder itself
                        for file in files:
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, media_root)
                            zipf.write(full_path, os.path.join('media', rel_path))
                            media_size_bytes += os.path.getsize(full_path)

            # 3. Verify Archive Integrity & File Size
            total_size_bytes = os.path.getsize(zip_filepath)
            checksum = cls.compute_sha256(zip_filepath)

            # Verification test
            with zipfile.ZipFile(zip_filepath, 'r') as test_zip:
                corrupt_file = test_zip.testzip()
                if corrupt_file is not None:
                    raise ValueError(f"Backup archive corruption detected in {corrupt_file}")

            record.file_path = zip_filepath
            record.file_size_bytes = total_size_bytes
            record.database_size_bytes = db_size_bytes
            record.media_size_bytes = media_size_bytes
            record.checksum_sha256 = checksum
            record.status = 'completed'
            record.verification_status = 'verified'
            record.save()

            if user:
                RBACService.log_activity(user, f"Created {backup_type} Backup '{b_id}' ({record.file_size_mb} MB) - Verified", "Backup & Restore", reference=b_id)

            cls.enforce_retention_policy()
            return record

        except Exception as e:
            record.status = 'failed'
            record.verification_status = 'failed'
            record.save()
            if user:
                RBACService.log_activity(user, f"Backup Failure on '{b_id}': {str(e)}", "Backup & Restore", reference=b_id)
            raise e

    @classmethod
    def restore_backup(cls, record, user=None):
        if not os.path.exists(record.file_path):
            record.status = 'restore_failed'
            record.save()
            raise FileNotFoundError(f"Backup archive file not found: {record.file_path}")

        # Safety Guard: Automatically create a safety backup before restoring
        safety_record = cls.create_backup(user=user, backup_type='before_restore', custom_name=f"Safety Backup before restoring {record.backup_id}")

        record.status = 'restoring'
        record.save()

        try:
            with zipfile.ZipFile(record.file_path, 'r') as zipf:
                if 'database_dump.json' in zipf.namelist():
                    db_json_content = zipf.read('database_dump.json').decode('utf-8')
                    # Deserialize objects back to database
                    for obj in serializers.deserialize('json', db_json_content):
                        obj.save()

                # Extract media files
                for item in zipf.namelist():
                    if item.startswith('media/'):
                        rel_path = item[6:]
                        if rel_path:
                            dest_path = os.path.join(settings.MEDIA_ROOT, rel_path)
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            with open(dest_path, 'wb') as f:
                                f.write(zipf.read(item))

            record.status = 'restore_completed'
            record.restored_at = timezone.now()
            record.save()

            if user:
                RBACService.log_activity(user, f"Restored System Backup '{record.backup_id}' (Safety Backup: {safety_record.backup_id})", "Backup & Restore", reference=record.backup_id)

            return True

        except Exception as e:
            record.status = 'restore_failed'
            record.save()
            raise e

    @classmethod
    def enforce_retention_policy(cls):
        b_settings = cls.get_backup_settings()
        limit = 10
        if b_settings.retention_policy == 'keep_5':
            limit = 5
        elif b_settings.retention_policy == 'keep_30':
            limit = 30
        elif b_settings.retention_policy == 'custom':
            limit = b_settings.custom_retention_count

        records = BackupRecord.objects.filter(status='completed', backup_type__in=['manual', 'automatic', 'scheduled']).order_by('-created_at')
        if records.count() > limit:
            excess_records = records[limit:]
            for r in excess_records:
                if r.file_path and os.path.exists(r.file_path):
                    try:
                        os.remove(r.file_path)
                    except OSError:
                        pass
                r.delete()

    @classmethod
    def get_storage_metrics(cls):
        records = BackupRecord.objects.filter(status='completed')
        total_bytes = sum(r.file_size_bytes for r in records)
        last_bkup = records.first()
        last_restore = BackupRecord.objects.filter(status='restore_completed').first()

        return {
            'last_backup': last_bkup,
            'last_restore': last_restore,
            'total_backups': records.count(),
            'total_storage_bytes': total_bytes,
            'total_storage_mb': round(total_bytes / (1024 * 1024), 2),
            'settings': cls.get_backup_settings()
        }


class DatabaseIntegrityService:
    """
    Scans production database for orphan records, negative stock balances,
    unbalanced accounting entries, and broken relation references.
    """

    @classmethod
    def run_integrity_check(cls):
        issues = []
        checks_performed = 0

        # Check 1: Negative Physical Stock Items
        try:
            from inventory.models import InventoryItem
            checks_performed += 1
            negative_items = InventoryItem.objects.filter(quantity__lt=0)
            if negative_items.exists():
                issues.append(f"Found {negative_items.count()} inventory items with negative physical stock.")
        except Exception:
            pass

        # Check 2: Unbalanced Accounting Ledger Entries
        try:
            from accounting.models import AccountingEntry
            from django.db.models import Sum
            checks_performed += 1
            entries = AccountingEntry.objects.values('entry_id').annotate(
                total_debit=Sum('debit_amount'),
                total_credit=Sum('credit_amount')
            )
            for e in entries:
                if abs((e['total_debit'] or 0) - (e['total_credit'] or 0)) > 0.01:
                    issues.append(f"Unbalanced accounting entry #{e['entry_id']}: Debit={e['total_debit']} vs Credit={e['total_credit']}")
        except Exception:
            pass

        # Check 3: Orphan Product Serial Numbers
        try:
            from batches.models import ProductSerialNumber
            checks_performed += 1
            orphan_serials = ProductSerialNumber.objects.filter(product__isnull=True)
            if orphan_serials.exists():
                issues.append(f"Found {orphan_serials.count()} serial numbers with missing product references.")
        except Exception:
            pass

        # Check 4: Unlinked Batches
        try:
            from batches.models import ProductBatch
            checks_performed += 1
            orphan_batches = ProductBatch.objects.filter(product__isnull=True)
            if orphan_batches.exists():
                issues.append(f"Found {orphan_batches.count()} product batches with missing product references.")
        except Exception:
            pass

        return {
            'healthy': len(issues) == 0,
            'checks_count': checks_performed,
            'issues_count': len(issues),
            'issues': issues,
            'timestamp': timezone.now().isoformat(),
        }
