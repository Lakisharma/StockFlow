from rest_framework import serializers
from .models import SystemAuditLog

class SystemAuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SystemAuditLog
        fields = [
            'id', 'log_id', 'timestamp', 'user', 'username', 'user_role',
            'action', 'module', 'record_type', 'record_id', 'description',
            'status', 'status_display', 'ip_address', 'device_info',
            'before_data', 'after_data', 'changed_fields'
        ]
        read_only_fields = fields  # Immutable audit logs
