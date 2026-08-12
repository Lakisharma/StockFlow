from django.db import models
from django.contrib.auth.models import User
from payments.models import PaymentAccount
from products.models import Warehouse

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Expense Categories'

    def __str__(self):
        return self.name

class Expense(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('card', 'Credit/Debit Card'),
        ('other', 'Other'),
    )

    expense_number = models.CharField(max_length=50, unique=True, db_index=True)
    expense_date = models.DateField()
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='bank_transfer')
    account = models.ForeignKey(PaymentAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_created')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_approved')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.expense_number} - {self.category.name} (₹{self.amount})"

class FinancialPeriod(models.Model):
    period_name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.period_name} ({'Locked' if self.is_locked else 'Active'})"
