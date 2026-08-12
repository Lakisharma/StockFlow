from django.db import models
from django.contrib.auth.models import User
from products.models import Product, Warehouse

class StockTransfer(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('in_transit', 'In Transit'),
        ('partially_received', 'Partially Received'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    transfer_number = models.CharField(max_length=50, unique=True)
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='outgoing_transfers')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='incoming_transfers')
    transfer_date = models.DateField()
    expected_arrival_date = models.DateField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    
    total_products = models.IntegerField(default=0)
    total_quantity = models.IntegerField(default=0)
    
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='requested_transfers')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_transfers')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transfers')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transfer_number}: {self.from_warehouse.name} -> {self.to_warehouse.name}"

class StockTransferItem(models.Model):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    available_stock_snapshot = models.IntegerField(default=0)
    requested_quantity = models.IntegerField(default=1)
    transferred_quantity = models.IntegerField(default=1)
    received_quantity = models.IntegerField(default=0)
    remarks = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.product.name} ({self.transferred_quantity}) in {self.transfer.transfer_number}"

    @property
    def difference_quantity(self):
        return max(self.transferred_quantity - self.received_quantity, 0)

class StockTransferHistory(models.Model):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transfer.transfer_number} - {self.action} at {self.created_at}"
