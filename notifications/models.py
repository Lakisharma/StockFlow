from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    TYPE_CHOICES = [
        ('low_stock', 'Low Stock Alert'),
        ('out_of_stock', 'Out of Stock Alert'),
        ('over_stock', 'Over Stock Alert'),
        ('purchase', 'Purchase Alert'),
        ('transfer', 'Stock Transfer Alert'),
        ('ocr', 'AI OCR Scanner Alert'),
        ('payment_due', 'Payment Due Alert'),
        ('backup', 'Backup Alert'),
        ('security', 'Security Alert'),
        ('system', 'System Message'),
    ]

    PRIORITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='system')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    module = models.CharField(max_length=50, default='System')
    related_record_type = models.CharField(max_length=50, blank=True, null=True)
    related_record_id = models.CharField(max_length=50, blank=True, null=True)
    action_url = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title} ({self.user.username})"

class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    notify_low_stock = models.BooleanField(default=True)
    notify_out_of_stock = models.BooleanField(default=True)
    notify_purchases = models.BooleanField(default=True)
    notify_transfers = models.BooleanField(default=True)
    notify_ocr = models.BooleanField(default=True)
    notify_backups = models.BooleanField(default=True)
    notify_security = models.BooleanField(default=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"
