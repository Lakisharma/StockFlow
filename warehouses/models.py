from django.db import models
from django.contrib.auth.models import User
from products.models import Warehouse, Product

class WarehouseZone(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='zones')
    zone_code = models.CharField(max_length=50)
    zone_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    capacity = models.IntegerField(default=1000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['zone_code']
        unique_together = ('warehouse', 'zone_code')

    def __str__(self):
        return f"{self.zone_name} ({self.zone_code}) - {self.warehouse.name}"

class WarehouseBin(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    zone = models.ForeignKey(WarehouseZone, on_delete=models.CASCADE, related_name='bins')
    bin_code = models.CharField(max_length=50, unique=True, db_index=True)
    rack = models.CharField(max_length=50, blank=True)
    shelf = models.CharField(max_length=50, blank=True)
    bin_number = models.CharField(max_length=50, blank=True)
    capacity = models.IntegerField(default=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['bin_code']

    def __str__(self):
        return f"{self.bin_code} (Zone {self.zone.zone_code})"

class WarehouseReorderSetting(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='reorder_settings')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='warehouse_reorders')
    minimum_stock = models.IntegerField(default=10)
    maximum_stock = models.IntegerField(default=500)
    reorder_level = models.IntegerField(default=20)
    reorder_quantity = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('warehouse', 'product')

    def __str__(self):
        return f"{self.product.name} at {self.warehouse.name} (Min: {self.minimum_stock}, Reorder: {self.reorder_level})"

class WarehouseUserAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='warehouse_accesses')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='user_accesses')
    can_manage = models.BooleanField(default=False)
    can_transfer = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'warehouse')

    def __str__(self):
        return f"{self.user.username} access to {self.warehouse.name}"
