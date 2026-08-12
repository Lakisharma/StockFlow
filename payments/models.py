from django.db import models
from django.contrib.auth.models import User
from sales.models import Customer, SalesInvoice
from suppliers.models import Supplier
from purchases.models import Purchase

class PaymentAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = (
        ('cash', 'Cash in Hand'),
        ('bank', 'Bank Account'),
        ('upi', 'UPI / Wallet'),
        ('other', 'Other Account'),
    )

    account_name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='bank')
    bank_name = models.CharField(max_length=100, blank=True)
    account_number_masked = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_name} ({self.get_account_type_display()})"

class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = (
        ('customer_payment', 'Customer Payment'),
        ('supplier_payment', 'Supplier Payment'),
        ('customer_refund', 'Customer Refund'),
        ('supplier_refund', 'Supplier Refund'),
        ('advance_received', 'Advance Received'),
        ('advance_paid', 'Advance Paid'),
    )

    METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('card', 'Credit/Debit Card'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('completed', 'Completed'),
        ('reversed', 'Reversed'),
        ('cancelled', 'Cancelled'),
    )

    payment_number = models.CharField(max_length=50, unique=True, db_index=True)
    payment_date = models.DateField()
    payment_type = models.CharField(max_length=30, choices=PAYMENT_TYPE_CHOICES)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    sales_invoice = models.ForeignKey(SalesInvoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True, related_name='finance_payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='bank_transfer')
    reference_number = models.CharField(max_length=100, blank=True)
    account = models.ForeignKey(PaymentAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    reversal_reason = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payment_number} - ₹{self.amount}"

class PaymentAllocation(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='allocations')
    sales_invoice = models.ForeignKey(SalesInvoice, on_delete=models.SET_NULL, null=True, blank=True)
    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
