from django.db import models
from django.contrib.auth.models import User
from suppliers.models import Supplier
from products.models import Product, Warehouse
from purchases.models import Purchase

class OCRScan(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('needs_review', 'Needs Review'),
        ('failed', 'Failed'),
        ('converted', 'Converted to Purchase'),
    )

    FILE_TYPE_CHOICES = (
        ('image', 'Image Document'),
        ('pdf', 'PDF Document'),
    )

    scan_id = models.CharField(max_length=50, unique=True)
    document = models.FileField(upload_to='ocr/bills/')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='image')
    file_size = models.IntegerField(default=0, help_text="File size in bytes")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    overall_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Raw Extraction Outputs
    raw_extracted_text = models.TextField(blank=True)
    raw_extracted_json = models.TextField(blank=True, help_text="JSON representation of parsed OCR data")
    
    # Extracted Invoice Header Fields
    invoice_number = models.CharField(max_length=100, blank=True)
    invoice_date = models.DateField(blank=True, null=True)
    po_number = models.CharField(max_length=100, blank=True)
    supplier_raw_name = models.CharField(max_length=255, blank=True)
    supplier_gstin = models.CharField(max_length=50, blank=True)
    matched_supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='ocr_scans')
    
    # Extracted Valuation Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Selected Warehouse & Converted Purchase Reference
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='ocr_scans')
    created_purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True, related_name='ocr_scan')
    
    # Audit & User info
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    processing_time_seconds = models.FloatField(default=0.0)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.scan_id} - {self.original_filename} ({self.get_status_display()})"

class OCRScanItem(models.Model):
    scan = models.ForeignKey(OCRScan, on_delete=models.CASCADE, related_name='items')
    raw_product_name = models.CharField(max_length=255)
    matched_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    hsn_code = models.CharField(max_length=50, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(blank=True, null=True)
    quantity = models.IntegerField(default=1)
    free_quantity = models.IntegerField(default=0)
    unit_name = models.CharField(max_length=50, default='PCS')
    rate = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=90.00)

    def __str__(self):
        return f"{self.raw_product_name} ({self.quantity}) in {self.scan.scan_id}"

class OCRScanAudit(models.Model):
    scan = models.ForeignKey(OCRScan, on_delete=models.CASCADE, related_name='audits')
    action = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.scan.scan_id} - {self.action} by {self.user}"
