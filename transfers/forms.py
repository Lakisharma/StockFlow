from django import forms
from products.models import Warehouse, Product
from .models import StockTransfer, StockTransferItem

class StockTransferForm(forms.ModelForm):
    class Meta:
        model = StockTransfer
        fields = [
            'transfer_number', 'transfer_date', 'from_warehouse', 'to_warehouse',
            'expected_arrival_date', 'priority', 'status', 'notes'
        ]
        widgets = {
            'transfer_number': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'e.g. TRF-20260809-001'}),
            'transfer_date': forms.DateInput(attrs={'class': 'input-control', 'type': 'date'}),
            'from_warehouse': forms.Select(attrs={'class': 'input-control', 'id': 'id_from_warehouse'}),
            'to_warehouse': forms.Select(attrs={'class': 'input-control', 'id': 'id_to_warehouse'}),
            'expected_arrival_date': forms.DateInput(attrs={'class': 'input-control', 'type': 'date'}),
            'priority': forms.Select(attrs={'class': 'input-control'}),
            'status': forms.Select(attrs={'class': 'input-control'}),
            'notes': forms.Textarea(attrs={'class': 'input-control', 'rows': 3, 'placeholder': 'Transfer notes or instructions...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        from_wh = cleaned_data.get('from_warehouse')
        to_wh = cleaned_data.get('to_warehouse')

        if from_wh and to_wh and from_wh == to_wh:
            raise forms.ValidationError("From Warehouse and To Warehouse cannot be the same location.")
        return cleaned_data

class StockTransferRejectForm(forms.Form):
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'input-control', 'rows': 3, 'placeholder': 'Enter reason for rejecting transfer request...'})
    )
