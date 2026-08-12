from django.db import models
from django.contrib.auth.models import User

class BackupRecord(models.Model):
    TYPE_CHOICES = [
        ('manual', 'Manual Backup'),
        ('automatic', 'Automatic Scheduled'),
        ('scheduled', 'Scheduled System Backup'),
        ('before_restore', 'Safety Backup (Before Restore)'),
        ('before_update', 'Pre-Update Safety Backup'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('restoring', 'Restoring'),
        ('restore_completed', 'Restore Completed'),
        ('restore_failed', 'Restore Failed'),
    ]

    VERIFICATION_CHOICES = [
        ('verified', 'Verified Integrity'),
        ('failed', 'Verification Failed'),
        ('pending', 'Pending Verification'),
    ]

    backup_id = models.CharField(max_length=50, unique=True)
    backup_name = models.CharField(max_length=150)
    backup_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='manual')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    verification_status = models.CharField(max_length=30, choices=VERIFICATION_CHOICES, default='pending')
    file_path = models.CharField(max_length=255, blank=True, null=True)
    file_size_bytes = models.BigIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64, blank=True, null=True)
    database_size_bytes = models.BigIntegerField(default=0)
    media_size_bytes = models.BigIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='backups_created')
    created_at = models.DateTimeField(auto_now_add=True)
    restored_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.backup_id} ({self.get_backup_type_display()}) - {self.get_status_display()}"

    @property
    def file_size_mb(self):
        return round(self.file_size_bytes / (1024 * 1024), 2)

class BackupSettings(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    RETENTION_CHOICES = [
        ('keep_5', 'Keep Last 5 Backups'),
        ('keep_10', 'Keep Last 10 Backups'),
        ('keep_30', 'Keep Last 30 Backups'),
        ('custom', 'Custom Retention Count'),
    ]

    auto_backup_enabled = models.BooleanField(default=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    backup_time = models.CharField(max_length=10, default='02:00')
    retention_policy = models.CharField(max_length=20, choices=RETENTION_CHOICES, default='keep_10')
    custom_retention_count = models.IntegerField(default=10)
    storage_location = models.CharField(max_length=100, default='Local Server Storage')

    def __str__(self):
        return f"Backup Settings (Auto: {self.auto_backup_enabled})"
