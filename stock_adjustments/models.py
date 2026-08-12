from django.db import models
from django.contrib.auth.models import User
from products.models import Product, Warehouse

class DamagedStockItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='damaged_items')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='damaged_items')
    quantity = models.IntegerField(default=0)
    reason = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Damaged: {self.product.name} ({self.quantity}) at {self.warehouse.name}"
