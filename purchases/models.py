from django.db import models
from django.contrib.auth.models import User
from suppliers.models import Supplier
from products.models import Product, Warehouse

class PurchaseOrder(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('partially_received', 'Partially Received'),
        ('received', 'Received / Fully Received'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    )

    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='purchase_orders')
    order_date = models.DateField()
    expected_delivery_date = models.DateField(blank=True, null=True)
    payment_terms = models.CharField(max_length=100, blank=True, default='Net 30')
    terms_conditions = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    approval_notes = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_created')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_approved')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.quantity}) in {self.purchase_order.po_number}"

class Purchase(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('pending', 'Pending'),
        ('overdue', 'Overdue'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
        ('card', 'Card'),
        ('credit', 'Credit'),
        ('other', 'Other'),
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    purchase_order_number = models.CharField(max_length=50, blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchases')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='purchases')
    purchase_date = models.DateField()
    expected_delivery_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    round_off = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pending_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Payment Info
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='credit')
    
    # Document Uploads
    invoice_file = models.FileField(upload_to='purchases/invoices/', blank=True, null=True)
    supporting_document = models.FileField(upload_to='purchases/documents/', blank=True, null=True)
    
    # Notes
    supplier_notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Purchase Invoice {self.invoice_number} - {self.supplier.name}"

    def update_payment_balance(self):
        completed_payments = self.payments.filter(status='completed')
        total_paid = sum(pay.amount for pay in completed_payments)
        self.paid_amount = total_paid
        self.pending_amount = max(self.grand_total - self.paid_amount, 0)
        
        if self.paid_amount >= self.grand_total:
            self.payment_status = 'paid'
        elif self.paid_amount > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'pending'
            
        self.save(update_fields=['paid_amount', 'pending_amount', 'payment_status'])

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    free_quantity = models.IntegerField(default=0)
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.quantity}) in {self.purchase.invoice_number}"

class PurchasePayment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
        ('card', 'Card'),
        ('credit', 'Credit'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='completed')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment of {self.amount} for {self.purchase.invoice_number}"

class PurchaseReturn(models.Model):
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='returns')
    return_number = models.CharField(max_length=50, unique=True)
    return_date = models.DateField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='purchase_returns')
    reason = models.TextField(blank=True)
    total_return_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='requested')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Return {self.return_number} for {self.purchase.invoice_number}"

class PurchaseReturnItem(models.Model):
    purchase_return = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    return_quantity = models.IntegerField(default=1)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.return_quantity}) in return {self.purchase_return.return_number}"

class GoodsReceiptNote(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft GRN'),
        ('inspected', 'Inspected'),
        ('confirmed', 'Confirmed & Inventory Updated'),
        ('rejected', 'Rejected'),
    )
    QUALITY_STATUS_CHOICES = (
        ('passed', 'Quality Passed'),
        ('failed', 'Quality Failed'),
        ('partial', 'Partial Pass'),
    )

    grn_number = models.CharField(max_length=50, unique=True, db_index=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='grns')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='grns')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='grns')
    received_date = models.DateField()
    challan_number = models.CharField(max_length=100, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    quality_status = models.CharField(max_length=30, choices=QUALITY_STATUS_CHOICES, default='passed')
    inspection_notes = models.TextField(blank=True)
    inspected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='grn_inspections')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='grns_created')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Goods Receipt Notes'

    def __str__(self):
        return f"{self.grn_number} - {self.supplier.name} ({self.get_status_display()})"

class GRNItem(models.Model):
    grn = models.ForeignKey(GoodsReceiptNote, on_delete=models.CASCADE, related_name='items')
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='grn_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    ordered_quantity = models.IntegerField(default=0)
    received_quantity = models.IntegerField(default=0)
    accepted_quantity = models.IntegerField(default=0)
    rejected_quantity = models.IntegerField(default=0)
    short_quantity = models.IntegerField(default=0)
    damaged_quantity = models.IntegerField(default=0)
    batch_number = models.CharField(max_length=100, blank=True)
    mfg_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    serial_numbers = models.JSONField(default=list, blank=True)
    rate = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.product.name} ({self.accepted_quantity} Accepted / {self.received_quantity} Received) in {self.grn.grn_number}"

