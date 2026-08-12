from django.db import models
from django.contrib.auth.models import User

class DocumentSequence(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ('invoice', 'Sales Invoice'),
        ('purchase_order', 'Purchase Order'),
        ('grn', 'Goods Receipt Note'),
        ('transfer', 'Stock Transfer'),
        ('adjustment', 'Stock Adjustment'),
        ('sales_return', 'Sales Return'),
        ('purchase_return', 'Purchase Return'),
        ('employee', 'Employee Code'),
        ('customer', 'Customer Code'),
        ('supplier', 'Supplier Code'),
    )

    document_type = models.CharField(max_length=40, choices=DOCUMENT_TYPE_CHOICES, unique=True, db_index=True)
    prefix = models.CharField(max_length=20, default='DOC-')
    next_number = models.IntegerField(default=1)
    padding = models.IntegerField(default=6, help_text="Number of digits e.g. 6 -> INV-000001")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['document_type']

    def __str__(self):
        formatted = f"{self.prefix}{self.next_number:0{self.padding}d}"
        return f"{self.get_document_type_display()}: Next -> '{formatted}'"

class SecurityPolicy(models.Model):
    max_failed_attempts = models.IntegerField(default=5)
    lockout_duration_mins = models.IntegerField(default=30)
    min_password_length = models.IntegerField(default=8)
    require_uppercase = models.BooleanField(default=True)
    require_number = models.BooleanField(default=True)
    require_special_char = models.BooleanField(default=True)
    inactivity_timeout_mins = models.IntegerField(default=30)
    enable_maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(default="StockFlow AI is currently undergoing scheduled maintenance. Please check back shortly.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Security Policies'

    def __str__(self):
        return f"Security Policy (Lockout: {self.max_failed_attempts} attempts, Maintenance: {self.enable_maintenance_mode})"

class UserFailedLogin(models.Model):
    username = models.CharField(max_length=150, db_index=True)
    ip_address = models.CharField(max_length=50, blank=True)
    attempt_time = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-attempt_time']

    def __str__(self):
        return f"Failed login for '{self.username}' at {self.attempt_time.strftime('%Y-%m-%d %H:%M:%S')}"
