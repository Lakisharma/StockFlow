from django.db import models
from django.contrib.auth.models import User
from products.models import Product, Warehouse

class StockMovement(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('purchase', 'Purchase'),
        ('purchase_return', 'Purchase Return'),
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
        ('transfer_in', 'Stock Transfer In'),
        ('transfer_out', 'Stock Transfer Out'),
        ('adjustment', 'Stock Adjustment'),
        ('opening_stock', 'Opening Stock'),
        ('damaged', 'Damaged'),
        ('expired', 'Expired'),
        ('other', 'Other'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_movements')
    batch = models.ForeignKey('batches.ProductBatch', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    serial = models.ForeignKey('batches.ProductSerialNumber', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    transaction_type = models.CharField(max_length=40, choices=TRANSACTION_TYPE_CHOICES)
    quantity = models.IntegerField(help_text="Signed integer: positive for stock addition, negative for stock deduction")
    previous_stock = models.IntegerField(default=0)
    new_stock = models.IntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reference_number = models.CharField(max_length=100, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stock Movements'

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} ({self.quantity}) at {self.warehouse.name}"

class StockAdjustment(models.Model):
    REASON_CHOICES = (
        ('audit_discrepancy', 'Physical Audit Discrepancy'),
        ('damaged_goods', 'Damaged Goods'),
        ('expired_stock', 'Expired Stock'),
        ('found_stock', 'Found / Extra Stock'),
        ('theft_loss', 'Theft / Mysterious Loss'),
        ('other', 'Other Reason'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_adjustments')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_adjustments')
    current_stock = models.IntegerField(default=0)
    physical_stock = models.IntegerField(default=0)
    difference_quantity = models.IntegerField(default=0, help_text="Physical Stock minus Current Stock")
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, default='audit_discrepancy')
    notes = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stock Adjustments'

    def __str__(self):
        return f"Adjustment {self.product.name} ({self.difference_quantity}) at {self.warehouse.name}"
