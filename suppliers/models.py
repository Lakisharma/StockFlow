from django.db import models

class Supplier(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    
    SUPPLIER_TYPE_CHOICES = (
        ('manufacturer', 'Manufacturer'),
        ('distributor', 'Distributor'),
        ('wholesaler', 'Wholesaler'),
        ('retailer', 'Retailer'),
    )
    
    TAX_REG_TYPE_CHOICES = (
        ('regular', 'Regular'),
        ('composition', 'Composition'),
        ('unregistered', 'Unregistered'),
    )
    
    # SECTION 1 — BASIC INFORMATION
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=100, unique=True)
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150)
    supplier_type = models.CharField(max_length=30, choices=SUPPLIER_TYPE_CHOICES, default='distributor')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    logo = models.ImageField(upload_to='suppliers/', blank=True, null=True)
    
    # SECTION 2 — CONTACT INFORMATION
    phone = models.CharField(max_length=30)
    alternate_phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # SECTION 3 — ADDRESS
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=20)
    
    # SECTION 4 — TAX INFORMATION
    gstin = models.CharField(max_length=30, blank=True)
    pan = models.CharField(max_length=30, blank=True)
    tax_reg_type = models.CharField(max_length=30, choices=TAX_REG_TYPE_CHOICES, default='regular')
    
    # SECTION 5 — BANK DETAILS
    bank_name = models.CharField(max_length=150, blank=True)
    holder_name = models.CharField(max_length=150, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=30, blank=True)
    branch = models.CharField(max_length=100, blank=True)
    
    # SECTION 6 — PAYMENT INFORMATION
    payment_terms = models.CharField(max_length=100, default='Net 30', help_text="e.g. Net 30, Net 60, COD")
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_days = models.IntegerField(default=30)
    
    # SECTION 7 — NOTES
    notes = models.TextField(blank=True)
    internal_remarks = models.TextField(blank=True)
    
    # AUDIT
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} ({self.code})"

class SupplierHistory(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='histories')
    action = models.CharField(max_length=100)
    detail = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Supplier Histories'
        
    def __str__(self):
        return f"{self.supplier.name} - {self.action} on {self.created_at}"
