from django.db import models
from django.contrib.auth.models import User

class SystemAuditLog(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('unauthorized', 'Unauthorized / Denied'),
    ]

    log_id = models.CharField(max_length=50, unique=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_activity_logs')
    user_role = models.CharField(max_length=50, default='System User')
    action = models.CharField(max_length=50, db_index=True)
    module = models.CharField(max_length=50, db_index=True)
    record_type = models.CharField(max_length=50, blank=True, null=True)
    record_id = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    device_info = models.CharField(max_length=255, blank=True, null=True)
    before_data = models.JSONField(blank=True, null=True)
    after_data = models.JSONField(blank=True, null=True)
    changed_fields = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.log_id}] {self.user.username if self.user else 'System'} - {self.action} on {self.module}"

class AuditLogSettings(models.Model):
    retention_days = models.IntegerField(default=90)
    log_views_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"Audit Settings (Retention: {self.retention_days} Days)"
