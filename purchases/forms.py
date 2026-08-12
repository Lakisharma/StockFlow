from django import forms
from .models import Purchase, PurchaseOrder, PurchaseReturn, PurchasePayment, PurchaseItem

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = [
            'invoice_number', 'purchase_order_number', 'supplier', 'warehouse',
            'purchase_date', 'expected_delivery_date', 'status',
            'payment_method', 'invoice_file', 'supporting_document',
            'supplier_notes', 'internal_notes',
            
            # Totals will be updated via calculations, but let's expose them as hidden or read-only
            'subtotal', 'discount_amount', 'tax_amount', 'round_off', 'grand_total'
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'INV-12345'}),
            'purchase_order_number': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'PO-12345 (Optional)'}),
            'supplier': forms.Select(attrs={'class': 'input-control'}),
            'warehouse': forms.Select(attrs={'class': 'input-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'input-control', 'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'class': 'input-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'input-control'}),
            'payment_method': forms.Select(attrs={'class': 'input-control'}),
            'invoice_file': forms.ClearableFileInput(attrs={'class': 'input-control-file'}),
            'supporting_document': forms.ClearableFileInput(attrs={'class': 'input-control-file'}),
            'supplier_notes': forms.Textarea(attrs={'class': 'input-control', 'rows': 2, 'placeholder': 'Supplier terms, comments...'}),
            'internal_notes': forms.Textarea(attrs={'class': 'input-control', 'rows': 2, 'placeholder': 'Internal records, inspection logs...'}),
            
            # Totals
            'subtotal': forms.NumberInput(attrs={'class': 'input-control', 'readonly': 'readonly'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'input-control', 'readonly': 'readonly'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'input-control', 'readonly': 'readonly'}),
            'round_off': forms.NumberInput(attrs={'class': 'input-control', 'readonly': 'readonly'}),
            'grand_total': forms.NumberInput(attrs={'class': 'input-control', 'readonly': 'readonly'}),
        }

    def clean_invoice_number(self):
        invoice_number = self.cleaned_data.get('invoice_number')
        if not invoice_number:
            raise forms.ValidationError("Invoice number is required.")
        # Check uniqueness
        instance = self.instance
        qs = Purchase.objects.filter(invoice_number__iexact=invoice_number)
        if instance and instance.pk:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise forms.ValidationError("Invoice number must be unique.")
        return invoice_number

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            'po_number', 'supplier', 'warehouse', 'order_date', 'expected_delivery_date',
            'subtotal', 'discount_amount', 'tax_amount', 'grand_total', 'notes', 'status'
        ]
        widgets = {
            'po_number': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'PO-12345'}),
            'supplier': forms.Select(attrs={'class': 'input-control'}),
            'warehouse': forms.Select(attrs={'class': 'input-control'}),
            'order_date': forms.DateInput(attrs={'class': 'input-control', 'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'class': 'input-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'input-control', 'rows': 2, 'placeholder': 'Notes...'}),
            'status': forms.Select(attrs={'class': 'input-control'}),
            'subtotal': forms.NumberInput(attrs={'class': 'input-control', 'readonly': 'readonly'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'input-control', 'readonly': 'readonly'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'input-control', 'readonly': 'readonly'}),
            'grand_total': forms.NumberInput(attrs={'class': 'input-control', 'readonly': 'readonly'}),
        }

class PurchaseReturnForm(forms.ModelForm):
    class Meta:
        model = PurchaseReturn
        fields = ['purchase', 'return_number', 'return_date', 'warehouse', 'reason', 'total_return_amount', 'status']
        widgets = {
            'purchase': forms.Select(attrs={'class': 'input-control'}),
            'return_number': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'PR-12345'}),
            'return_date': forms.DateInput(attrs={'class': 'input-control', 'type': 'date'}),
            'warehouse': forms.Select(attrs={'class': 'input-control'}),
            'reason': forms.Textarea(attrs={'class': 'input-control', 'rows': 2, 'placeholder': 'Reason for return...'}),
            'total_return_amount': forms.NumberInput(attrs={'class': 'input-control', 'readonly': 'readonly'}),
            'status': forms.Select(attrs={'class': 'input-control'}),
        }

class PurchasePaymentForm(forms.ModelForm):
    class Meta:
        model = PurchasePayment
        fields = ['purchase', 'amount', 'payment_date', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'purchase': forms.Select(attrs={'class': 'input-control', 'style': 'display:none;'}),
            'amount': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'input-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'input-control'}),
            'reference_number': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Ref / Txn ID'}),
            'notes': forms.Textarea(attrs={'class': 'input-control', 'rows': 2, 'placeholder': 'Receipt notes...'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Payment amount must be greater than zero.")
        
        # Check if payment exceeds pending amount (unless overpayment is supported)
        purchase = self.cleaned_data.get('purchase')
        if purchase and amount:
            # Calculate current pending amount before this new payment
            pending = purchase.grand_total - purchase.paid_amount
            # When updating a payment, we should subtract the previous value of this payment from paid_amount first.
            if self.instance and self.instance.pk:
                pending += self.instance.amount
            if amount > pending:
                raise forms.ValidationError(f"Payment amount (${amount:.2f}) cannot exceed the pending balance (${pending:.2f}).")
        return amount
