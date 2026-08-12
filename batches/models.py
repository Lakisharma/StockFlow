from django.db import models
from django.utils import timezone
from products.models import Product, Warehouse
from suppliers.models import Supplier

class ProductBatch(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active Stock'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('recalled', 'Recalled'),
        ('exhausted', 'Exhausted'),
    ]

    batch_number = models.CharField(max_length=100, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='batches')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='batches')
    purchase_invoice = models.CharField(max_length=100, blank=True)
    mfg_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    initial_quantity = models.IntegerField(default=0)
    available_quantity = models.IntegerField(default=0)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['expiry_date', '-created_at']
        unique_together = ('batch_number', 'product', 'warehouse')
        verbose_name_plural = 'Product Batches'

    def __str__(self):
        return f"Batch {self.batch_number} - {self.product.name} ({self.available_quantity} in {self.warehouse.name})"

    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        today = timezone.now().date()
        return (self.expiry_date - today).days

    @property
    def expiry_status(self):
        if not self.expiry_date:
            return 'No Expiry'
        days = self.days_until_expiry
        if days < 0:
            return 'Expired'
        elif days <= 30:
            return 'Expiring Soon'
        return 'Fresh'

    @property
    def inventory_value(self):
        return max(self.available_quantity, 0) * (self.purchase_price or self.product.purchase_price or 0.00)

class ProductSerialNumber(models.Model):
    STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('sold', 'Sold'),
        ('transferred', 'Transferred'),
        ('reserved', 'Reserved'),
        ('damaged', 'Damaged'),
        ('returned', 'Returned'),
        ('under_repair', 'Under Repair'),
        ('lost', 'Lost'),
        ('disposed', 'Disposed'),
    ]

    serial_number = models.CharField(max_length=100, unique=True, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='serials')
    batch = models.ForeignKey(ProductBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='serials')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='serials')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='serials')
    purchase_invoice = models.CharField(max_length=100, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    warranty_start = models.DateField(null=True, blank=True)
    warranty_end = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_stock')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Product Serial Numbers'

    def __str__(self):
        return f"S/N: {self.serial_number} - {self.product.name} ({self.get_status_display()})"

    @property
    def warranty_status(self):
        if not self.warranty_end:
            return 'N/A'
        today = timezone.now().date()
        days_left = (self.warranty_end - today).days
        if days_left < 0:
            return 'Expired'
        elif days_left <= 30:
            return 'Expiring Soon'
        return 'Active'
