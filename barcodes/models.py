from django.db import models
from django.contrib.auth.models import User
from products.models import Product, Warehouse

class BarcodeScanHistory(models.Model):
    SCAN_MODE_CHOICES = [
        ('lookup', 'Product Lookup'),
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
        ('purchase', 'Purchase Entry'),
        ('transfer', 'Stock Transfer'),
        ('counting', 'Stock Counting'),
    ]

    STATUS_CHOICES = [
        ('found', 'Product Found'),
        ('not_found', 'Product Not Found'),
        ('invalid', 'Invalid Barcode'),
        ('duplicate', 'Duplicate Barcode'),
    ]

    scan_id = models.CharField(max_length=50, unique=True, db_index=True)
    barcode_value = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='barcode_scans')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    scan_mode = models.CharField(max_length=30, choices=SCAN_MODE_CHOICES, default='lookup')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='found')
    quantity = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Barcode Scan Histories'

    def __str__(self):
        return f"[{self.scan_id}] Scanned '{self.barcode_value}' ({self.get_scan_mode_display()}) - {self.get_status_display()}"

class BarcodeLabelPreset(models.Model):
    name = models.CharField(max_length=50)
    width_mm = models.IntegerField(default=50)
    height_mm = models.IntegerField(default=30)
    show_product_name = models.BooleanField(default=True)
    show_price = models.BooleanField(default=True)
    show_sku = models.BooleanField(default=True)
    show_unit = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.width_mm}x{self.height_mm}mm)"

class ScanSession(models.Model):
    SCAN_MODE_CHOICES = [
        ('lookup', 'Product Lookup'),
        ('receiving', 'Goods Receiving'),
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
        ('transfer', 'Stock Transfer'),
        ('stock_count', 'Stock Counting'),
        ('bin_lookup', 'Bin Location Lookup'),
        ('batch_lookup', 'Batch Lookup'),
        ('serial_lookup', 'Serial Number Lookup'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    session_number = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scan_sessions')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='scan_sessions')
    scan_mode = models.CharField(max_length=30, choices=SCAN_MODE_CHOICES, default='lookup')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    total_scans = models.IntegerField(default=0)
    successful_scans = models.IntegerField(default=0)
    failed_scans = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"Session {self.session_number} ({self.get_scan_mode_display()}) at {self.warehouse.name}"

class ScanSessionItem(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
    ]

    session = models.ForeignKey(ScanSession, on_delete=models.CASCADE, related_name='items')
    barcode_value = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    message = models.CharField(max_length=255, blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scanned_at']

    def __str__(self):
        return f"{self.barcode_value} in Session {self.session.session_number}"

