from django.db import models
from categories.models import Category
from brands.models import Brand
from units.models import Unit

class Warehouse(models.Model):
    WAREHOUSE_TYPE_CHOICES = (
        ('main', 'Main Warehouse'),
        ('godown', 'Godown'),
        ('branch', 'Branch'),
        ('distribution', 'Distribution Center'),
        ('store', 'Store'),
    )
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    
    # SECTION 1 — BASIC INFORMATION
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    warehouse_type = models.CharField(max_length=30, choices=WAREHOUSE_TYPE_CHOICES, default='godown')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    logo = models.ImageField(upload_to='warehouses/', blank=True, null=True)

    # SECTION 2 — CONTACT INFORMATION
    manager_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    alternate_phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    # SECTION 3 — ADDRESS
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    pin_code = models.CharField(max_length=20, blank=True)

    # SECTION 4 — CAPACITY
    total_capacity = models.IntegerField(default=10000, help_text="Configurable volume or weight limit")
    capacity_unit = models.CharField(max_length=50, default='Units', help_text="e.g. Sq Ft, Boxes, Units, Cartons")

    # SECTION 5 — ADDITIONAL INFORMATION
    opening_date = models.DateField(blank=True, null=True)
    operating_hours = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    # AUDIT
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.code})"

class Product(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    TAX_TYPE_CHOICES = (
        ('inclusive', 'Inclusive'),
        ('exclusive', 'Exclusive'),
    )
    
    # SECTION 1 — BASIC INFORMATION
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, blank=True)
    qr_code = models.ImageField(upload_to='products/qrcodes/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # SECTION 2 — PRICING
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    mrp = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="GST percentage (e.g. 18.00)")
    tax_type = models.CharField(max_length=20, choices=TAX_TYPE_CHOICES, default='exclusive')
    
    # SECTION 3 — INVENTORY
    opening_stock = models.IntegerField(default=0)
    current_stock = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=5)
    max_stock_level = models.IntegerField(default=1000)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    stock_alert = models.BooleanField(default=True)
    
    hsn_code = models.CharField(max_length=20, blank=True)
    product_code = models.CharField(max_length=100, blank=True)
    # SECTION 5 — ADDITIONAL INFORMATION
    weight = models.CharField(max_length=50, blank=True)
    dimensions = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=150, blank=True)
    country_of_origin = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    # SECTION 6 — BATCH & SERIAL TRACKING CONFIGURATION
    TRACKING_TYPE_CHOICES = [
        ('normal', 'Normal Product'),
        ('batch', 'Batch Tracking'),
        ('expiry', 'Expiry Tracking'),
        ('serial', 'Serial Number Tracking'),
        ('batch_expiry', 'Batch + Expiry'),
        ('batch_serial', 'Batch + Serial Number'),
        ('all', 'Batch + Expiry + Serial'),
    ]
    tracking_type = models.CharField(max_length=30, choices=TRACKING_TYPE_CHOICES, default='normal')
    has_batch_tracking = models.BooleanField(default=False)
    has_expiry_tracking = models.BooleanField(default=False)
    has_serial_tracking = models.BooleanField(default=False)
    require_mfg_date = models.BooleanField(default=False)
    require_exp_date = models.BooleanField(default=False)
    require_batch_no = models.BooleanField(default=False)
    require_serial_no = models.BooleanField(default=False)

    # AUDIT
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def stock_status(self):
        if self.current_stock <= 0:
            return 'Out of Stock'
        elif self.current_stock <= self.min_stock_level:
            return 'Low Stock'
        return 'In Stock'

class ProductHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='histories')
    action = models.CharField(max_length=100)
    detail = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Product Histories'
        
    def __str__(self):
        return f"{self.product.name} - {self.action} on {self.created_at}"

class WarehouseStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='warehouse_stocks')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='product_stocks')
    quantity = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=5)
    max_stock_level = models.IntegerField(default=1000)
    rack_location = models.CharField(max_length=100, blank=True, null=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'warehouse')
        verbose_name_plural = 'Warehouse Stocks'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.product.name} in {self.warehouse.name}: {self.quantity}"

    @property
    def stock_status(self):
        if self.quantity < 0:
            return 'Negative Stock'
        elif self.quantity == 0:
            return 'Out of Stock'
        elif self.quantity <= self.min_stock_level:
            return 'Low Stock'
        elif self.quantity > self.max_stock_level:
            return 'Over Stock'
        return 'In Stock'

    @property
    def inventory_value(self):
        return max(self.quantity, 0) * (self.product.purchase_price or 0.00)

class WarehouseHistory(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='histories')
    action = models.CharField(max_length=100)
    detail = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Warehouse Histories'

    def __str__(self):
        return f"{self.warehouse.name} - {self.action} on {self.created_at}"
