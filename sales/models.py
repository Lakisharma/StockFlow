from django.db import models
from django.contrib.auth.models import User
from products.models import Product, Warehouse

class Customer(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    customer_code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    business_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    gstin = models.CharField(max_length=20, blank=True)
    pan = models.CharField(max_length=20, blank=True)
    billing_address = models.TextField()
    shipping_address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    payment_terms = models.CharField(max_length=100, default='Net 30')
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    outstanding_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.customer_code})"

    @property
    def available_credit(self):
        return max(self.credit_limit - self.outstanding_amount, 0)

class SalesOrder(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('picking', 'Picking'),
        ('partially_fulfilled', 'Partially Fulfilled'),
        ('ready_for_dispatch', 'Ready for Dispatch'),
        ('dispatched', 'Dispatched'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    )

    so_number = models.CharField(max_length=50, unique=True, db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sales_orders')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='sales_orders')
    order_date = models.DateField()
    expected_dispatch_date = models.DateField(null=True, blank=True)
    payment_terms = models.CharField(max_length=100, default='Net 30')
    shipping_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    shipping_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.so_number} - {self.customer.name}"

class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    ordered_quantity = models.IntegerField(default=1)
    picked_quantity = models.IntegerField(default=0)
    dispatched_quantity = models.IntegerField(default=0)
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.ordered_quantity}) in {self.sales_order.so_number}"

class PickList(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    pick_list_number = models.CharField(max_length=50, unique=True, db_index=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='pick_lists')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pick_lists_assigned')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pick_list_number} for {self.sales_order.so_number}"

class PickListItem(models.Model):
    pick_list = models.ForeignKey(PickList, on_delete=models.CASCADE, related_name='items')
    so_item = models.ForeignKey(SalesOrderItem, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    ordered_quantity = models.IntegerField(default=1)
    picked_quantity = models.IntegerField(default=0)
    batch_number = models.CharField(max_length=100, blank=True)
    serial_numbers = models.JSONField(default=list, blank=True)

class Dispatch(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('ready', 'Ready for Dispatch'),
        ('dispatched', 'Dispatched'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    )

    dispatch_number = models.CharField(max_length=50, unique=True, db_index=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='dispatches')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    dispatch_date = models.DateField()
    transporter = models.CharField(max_length=100, blank=True)
    vehicle_number = models.CharField(max_length=50, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    driver_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='dispatched')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.dispatch_number} - {self.customer.name}"

class DispatchItem(models.Model):
    dispatch = models.ForeignKey(Dispatch, on_delete=models.CASCADE, related_name='items')
    so_item = models.ForeignKey(SalesOrderItem, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    dispatched_quantity = models.IntegerField(default=1)
    batch_number = models.CharField(max_length=100, blank=True)
    serial_numbers = models.JSONField(default=list, blank=True)
    rate = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

class SalesInvoice(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('cancelled', 'Cancelled'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    )

    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    dispatch = models.ForeignKey(Dispatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    invoice_date = models.DateField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    shipping_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='issued')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer.name}"

class SalesReturn(models.Model):
    return_number = models.CharField(max_length=50, unique=True, db_index=True)
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, related_name='returns')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    return_date = models.DateField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=30, default='approved')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Return {self.return_number} for {self.invoice.invoice_number}"

class SalesReturnItem(models.Model):
    sales_return = models.ForeignKey(SalesReturn, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    good_quantity = models.IntegerField(default=0)
    damaged_quantity = models.IntegerField(default=0)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
