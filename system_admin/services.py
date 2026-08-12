import os
from django.db import connection, transaction
from django.utils import timezone
from django.contrib.auth.models import User
from users.models import UserProfile
from audit_logs.models import SystemAuditLog
from backups.models import BackupRecord
from .models import DocumentSequence, SecurityPolicy, UserFailedLogin

class SystemAdminService:

    DEFAULT_PREFIXES = {
        'invoice': ('INV-', 6),
        'purchase_order': ('PO-', 6),
        'grn': ('GRN-', 6),
        'transfer': ('TRF-', 6),
        'adjustment': ('ADJ-', 6),
        'sales_return': ('SRN-', 6),
        'purchase_return': ('PRN-', 6),
        'employee': ('EMP-', 4),
        'customer': ('CUST-', 5),
        'supplier': ('SUP-', 5),
    }

    @classmethod
    @transaction.atomic
    def get_next_document_number(cls, document_type):
        default_prefix, default_padding = cls.DEFAULT_PREFIXES.get(document_type, ('DOC-', 6))
        seq, _ = DocumentSequence.objects.select_for_update().get_or_create(
            document_type=document_type,
            defaults={'prefix': default_prefix, 'padding': default_padding, 'next_number': 1}
        )
        formatted_number = f"{seq.prefix}{seq.next_number:0{seq.padding}d}"
        seq.next_number += 1
        seq.save()
        return formatted_number

    @classmethod
    def get_security_policy(cls):
        policy, _ = SecurityPolicy.objects.get_or_create(id=1)
        return policy

    @classmethod
    def register_failed_login(cls, username, ip_address='127.0.0.1'):
        UserFailedLogin.objects.create(username=username, ip_address=ip_address)
        policy = cls.get_security_policy()

        # Count recent unresolved failed attempts
        attempts_count = UserFailedLogin.objects.filter(username=username, is_resolved=False).count()
        
        user = User.objects.filter(username=username).first()
        if user and hasattr(user, 'profile'):
            if attempts_count >= policy.max_failed_attempts:
                user.profile.status = 'inactive'  # Lock account
                user.profile.save()
                return True, f"Account '{username}' locked due to {attempts_count} consecutive failed login attempts."
        return False, f"Failed attempt recorded for '{username}' ({attempts_count}/{policy.max_failed_attempts})."

    @classmethod
    def unlock_user_account(cls, user):
        if hasattr(user, 'profile'):
            user.profile.status = 'active'
            user.profile.save()
        UserFailedLogin.objects.filter(username=user.username, is_resolved=False).update(is_resolved=True)
        return True

    @classmethod
    def get_security_metrics(cls):
        policy = cls.get_security_policy()
        today = timezone.now().date()

        return {
            'policy': policy,
            'failed_logins_today': UserFailedLogin.objects.filter(attempt_time__date=today).count(),
            'locked_users_count': UserProfile.objects.filter(status='inactive').count(),
            'active_users_count': User.objects.filter(is_active=True).count(),
            'total_users_count': User.objects.count(),
        }

class SystemHealthService:

    @classmethod
    def run_health_check(cls):
        checks = {}

        # 1. Database Connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                checks['database'] = {'status': 'healthy', 'message': 'Database connection OK'}
        except Exception as e:
            checks['database'] = {'status': 'critical', 'message': f"Database connection error: {str(e)}"}

        # 2. File Storage Access
        try:
            media_dir = 'media/'
            os.makedirs(media_dir, exist_ok=True)
            checks['storage'] = {'status': 'healthy', 'message': 'File Storage writable'}
        except Exception as e:
            checks['storage'] = {'status': 'warning', 'message': f"Storage warning: {str(e)}"}

        # 3. System Backups
        last_backup = BackupRecord.objects.filter(status='success').first()
        if last_backup:
            checks['backup'] = {'status': 'healthy', 'message': f"Last successful backup: {last_backup.created_at.strftime('%Y-%m-%d %H:%M')}"}
        else:
            checks['backup'] = {'status': 'warning', 'message': 'No system backups found'}

        # 4. Audit Log System
        log_count = SystemAuditLog.objects.count()
        checks['audit_log'] = {'status': 'healthy', 'message': f"Audit logging active ({log_count} records)"}

        return checks
