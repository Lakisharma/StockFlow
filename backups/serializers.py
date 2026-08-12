from rest_framework import serializers
from .models import BackupRecord, BackupSettings

class BackupRecordSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    backup_type_display = serializers.CharField(source='get_backup_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    file_size_mb = serializers.ReadOnlyField()

    class Meta:
        model = BackupRecord
        fields = [
            'id', 'backup_id', 'backup_name', 'backup_type', 'backup_type_display',
            'status', 'status_display', 'verification_status', 'verification_status_display',
            'file_size_bytes', 'file_size_mb', 'checksum_sha256', 'database_size_bytes',
            'media_size_bytes', 'created_by', 'created_by_username', 'created_at', 'restored_at'
        ]

class BackupSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupSettings
        fields = '__all__'
