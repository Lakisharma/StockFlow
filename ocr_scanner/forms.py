import os
from django import forms
from suppliers.models import Supplier
from products.models import Warehouse
from .models import OCRScan

class BillUploadForm(forms.ModelForm):
    class Meta:
        model = OCRScan
        fields = ['document']
        widgets = {
            'document': forms.FileInput(attrs={'class': 'file-input', 'id': 'documentUpload', 'accept': '.jpg,.jpeg,.png,.webp,.pdf'})
        }

    def clean_document(self):
        doc = self.cleaned_data.get('document')
        if doc:
            ext = os.path.splitext(doc.name)[1].lower()
            valid_exts = ['.jpg', '.jpeg', '.png', '.webp', '.pdf']
            if ext not in valid_exts:
                raise forms.ValidationError(f"Unsupported file format '{ext}'. Allowed formats: JPG, JPEG, PNG, WEBP, PDF.")
            # 20MB file size limit check
            if doc.size > 20 * 1024 * 1024:
                raise forms.ValidationError("File size exceeds 20MB limit.")
        return doc

class OCRVerificationForm(forms.ModelForm):
    class Meta:
        model = OCRScan
        fields = [
            'invoice_number', 'invoice_date', 'po_number', 'matched_supplier',
            'warehouse', 'subtotal', 'tax_amount', 'discount_amount', 'grand_total'
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'input-control'}),
            'invoice_date': forms.DateInput(attrs={'class': 'input-control', 'type': 'date'}),
            'po_number': forms.TextInput(attrs={'class': 'input-control'}),
            'matched_supplier': forms.Select(attrs={'class': 'input-control'}),
            'warehouse': forms.Select(attrs={'class': 'input-control'}),
            'subtotal': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01'}),
            'grand_total': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01'}),
        }
