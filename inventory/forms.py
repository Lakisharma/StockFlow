from django import forms
from products.models import Product, Warehouse, WarehouseStock
from .models import StockMovement, StockAdjustment

class StockInForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'input-control'})
    )
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'input-control'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'input-control', 'placeholder': 'Enter quantity to add'})
    )
    unit_cost = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01', 'placeholder': 'Optional unit cost'})
    )
    reference_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'e.g. STK-IN-1001'})
    )
    reason = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Reason (e.g. New Purchase, Manual Restock)'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'input-control', 'rows': 3, 'placeholder': 'Additional notes...'})
    )

class StockOutForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'input-control'})
    )
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'input-control'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'input-control', 'placeholder': 'Enter quantity to remove'})
    )
    reference_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'e.g. STK-OUT-2001'})
    )
    reason = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Reason (e.g. Sales Dispatch, Damage, Internal Use)'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'input-control', 'rows': 3, 'placeholder': 'Additional notes...'})
    )

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        warehouse = cleaned_data.get('warehouse')
        quantity = cleaned_data.get('quantity')

        if product and warehouse and quantity:
            stock_obj = WarehouseStock.objects.filter(product=product, warehouse=warehouse).first()
            available = stock_obj.quantity if stock_obj else 0
            if quantity > available:
                raise forms.ValidationError(
                    f"Requested Stock Out quantity ({quantity}) exceeds available stock ({available}) in '{warehouse.name}'."
                )
        return cleaned_data

class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = StockAdjustment
        fields = ['product', 'warehouse', 'physical_stock', 'reason', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'input-control'}),
            'warehouse': forms.Select(attrs={'class': 'input-control'}),
            'physical_stock': forms.NumberInput(attrs={'class': 'input-control', 'min': '0'}),
            'reason': forms.Select(attrs={'class': 'input-control'}),
            'notes': forms.Textarea(attrs={'class': 'input-control', 'rows': 3, 'placeholder': 'Reason for adjustment variance...'}),
        }

class OpeningStockForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'input-control'})
    )
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'input-control'})
    )
    opening_quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'input-control', 'placeholder': 'Opening stock quantity'})
    )
    opening_rate = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01', 'placeholder': 'Opening unit cost rate'})
    )
    reference_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'e.g. OP-2026-001'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'input-control', 'rows': 2, 'placeholder': 'Notes...'})
    )
