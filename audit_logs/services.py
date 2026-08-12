import csv
import json
from io import StringIO
from django.utils import timezone
from django.db import models
from .models import SystemAuditLog, AuditLogSettings

class AuditLogService:

    SENSITIVE_KEYS = {'password', 'confirm_password', 'new_password', 'api_key', 'secret', 'token', 'access_token', 'private_key'}

    @classmethod
    def get_client_ip(cls, request):
        if not request:
            return None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @classmethod
    def get_device_info(cls, request):
        if not request:
            return None
        return request.META.get('HTTP_USER_AGENT', '')[:250]

    @classmethod
    def sanitize_dict(cls, data):
        if not isinstance(data, dict):
            return data
        sanitized = {}
        for k, v in data.items():
            if k.lower() in cls.SENSITIVE_KEYS:
                sanitized[k] = '***MASKED***'
            elif isinstance(v, dict):
                sanitized[k] = cls.sanitize_dict(v)
            else:
                sanitized[k] = str(v) if v is not None else None
        return sanitized

    @classmethod
    def compute_diff(cls, before_data, after_data):
        if not before_data or not after_data:
            return None

        diff = {}
        all_keys = set(before_data.keys()).union(set(after_data.keys()))
        for key in all_keys:
            val_before = before_data.get(key)
            val_after = after_data.get(key)
            if val_before != val_after:
                diff[key] = {
                    'before': val_before,
                    'after': val_after
                }
        return diff if diff else None

    @classmethod
    def log_event(cls, user, action, module, record_type=None, record_id=None, description='', status='success', before_data=None, after_data=None, request=None):
        timestamp_str = timezone.now().strftime('%Y%m%d%H%M%S')
        unique_suffix = timezone.now().strftime('%f')[:4]
        log_id = f"LOG-{timestamp_str}-{unique_suffix}"

        user_role = 'System User'
        if user and user.is_authenticated:
            if hasattr(user, 'profile') and user.profile.role:
                user_role = user.profile.role.name
            elif user.is_superuser:
                user_role = 'Super Admin'

        sanitized_before = cls.sanitize_dict(before_data) if before_data else None
        sanitized_after = cls.sanitize_dict(after_data) if after_data else None
        changed_fields = cls.compute_diff(sanitized_before, sanitized_after) if (sanitized_before and sanitized_after) else None

        log_entry = SystemAuditLog.objects.create(
            log_id=log_id,
            user=user if user and user.is_authenticated else None,
            user_role=user_role,
            action=action,
            module=module,
            record_type=record_type,
            record_id=str(record_id) if record_id else None,
            description=description,
            status=status,
            ip_address=cls.get_client_ip(request),
            device_info=cls.get_device_info(request),
            before_data=sanitized_before,
            after_data=sanitized_after,
            changed_fields=changed_fields
        )
        return log_entry

    @classmethod
    def get_audit_metrics(cls):
        today = timezone.now().date()
        logs_today = SystemAuditLog.objects.filter(timestamp__date=today)

        return {
            'total_activities': SystemAuditLog.objects.count(),
            'today_activities': logs_today.count(),
            'today_logins': logs_today.filter(action__icontains='Login').count(),
            'today_updates': logs_today.filter(action__icontains='Update').count(),
            'today_deletions': logs_today.filter(action__icontains='Delete').count(),
            'failed_actions': SystemAuditLog.objects.exclude(status='success').count(),
        }

    @classmethod
    def generate_csv(cls, queryset):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Log ID', 'Timestamp', 'User', 'Role', 'Action', 'Module', 'Record Type', 'Record ID', 'Description', 'Status', 'IP Address'])

        for log in queryset:
            writer.writerow([
                log.log_id,
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.user.username if log.user else 'System',
                log.user_role,
                log.action,
                log.module,
                log.record_type or '',
                log.record_id or '',
                log.description,
                log.status,
                log.ip_address or ''
            ])
        return output.getvalue()
