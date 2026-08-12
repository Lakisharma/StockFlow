import re
from django import forms
from .models import Supplier

class SupplierForm(forms.ModelForm):
    auto_generate_code = forms.BooleanField(required=False, initial=False, label="Auto Generate Supplier Code")

    class Meta:
        model = Supplier
        fields = [
            # Basic Info
            'name', 'code', 'company_name', 'contact_person', 'supplier_type', 'status', 'logo',
            # Contact Info
            'phone', 'alternate_phone', 'email', 'website',
            # Address
            'address', 'city', 'state', 'country', 'pin_code',
            # Tax Info
            'gstin', 'pan', 'tax_reg_type',
            # Bank Details
            'bank_name', 'holder_name', 'account_number', 'ifsc_code', 'branch',
            # Payment Info
            'payment_terms', 'credit_limit', 'opening_balance', 'outstanding_balance', 'due_days',
            # Notes
            'notes', 'internal_remarks'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Supplier Name'}),
            'code': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Unique Code (e.g. SUP-00001)'}),
            'company_name': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Company Name'}),
            'contact_person': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Contact Person Name'}),
            'supplier_type': forms.Select(attrs={'class': 'input-control'}),
            'status': forms.Select(attrs={'class': 'input-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'input-control-file'}),
            
            'phone': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Phone Number'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Alternate Phone'}),
            'email': forms.EmailInput(attrs={'class': 'input-control', 'placeholder': 'Email Address'}),
            'website': forms.URLInput(attrs={'class': 'input-control', 'placeholder': 'https://website.com'}),
            
            'address': forms.Textarea(attrs={'class': 'input-control', 'rows': 2, 'placeholder': 'Full Address...'}),
            'city': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'State'}),
            'country': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Country'}),
            'pin_code': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'PIN / ZIP Code'}),
            
            'gstin': forms.TextInput(attrs={'class': 'input-control', 'placeholder': '15-digit GSTIN'}),
            'pan': forms.TextInput(attrs={'class': 'input-control', 'placeholder': '10-digit PAN'}),
            'tax_reg_type': forms.Select(attrs={'class': 'input-control'}),
            
            'bank_name': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Bank Name'}),
            'holder_name': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Account Holder Name'}),
            'account_number': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Account Number'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'IFSC Code'}),
            'branch': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Branch Location'}),
            
            'payment_terms': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'e.g. Net 30, COD'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01', 'placeholder': '0.00'}),
            'opening_balance': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01', 'placeholder': '0.00'}),
            'outstanding_balance': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01', 'placeholder': '0.00'}),
            'due_days': forms.NumberInput(attrs={'class': 'input-control', 'placeholder': '30'}),
            
            'notes': forms.Textarea(attrs={'class': 'input-control', 'rows': 2, 'placeholder': 'Notes...'}),
            'internal_remarks': forms.Textarea(attrs={'class': 'input-control', 'rows': 2, 'placeholder': 'Internal Remarks...'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].required = False  # Required=False because it can be auto-generated

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Validate simple phone format (digits, spaces, hyphens, plus)
        if not re.match(r'^\+?[0-9\s\-]+$', phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_pin_code(self):
        pin_code = self.cleaned_data.get('pin_code')
        if not re.match(r'^[a-zA-Z0-9\s\-]+$', pin_code):
            raise forms.ValidationError("Enter a valid PIN / ZIP code.")
        return pin_code

    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        if account_number and not re.match(r'^[0-9]+$', account_number):
            raise forms.ValidationError("Account number must contain digits only.")
        return account_number

    def clean_gstin(self):
        gstin = self.cleaned_data.get('gstin')
        if gstin:
            # Simple format verification (15 alphanumeric characters)
            if len(gstin) != 15 or not re.match(r'^[a-zA-Z0-9]+$', gstin):
                raise forms.ValidationError("GSTIN must be exactly 15 alphanumeric characters.")
        return gstin

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        auto_generate_code = cleaned_data.get('auto_generate_code')
        
        # Auto-generate code if requested or empty
        if auto_generate_code or not code:
            prefix = "SUP"
            count = Supplier.objects.count() + 1
            new_code = f"{prefix}-{count:05d}"
            while Supplier.objects.filter(code=new_code).exists():
                count += 1
                new_code = f"{prefix}-{count:05d}"
            cleaned_data['code'] = new_code
        else:
            # Unique validation check
            instance = self.instance
            qs = Supplier.objects.filter(code__iexact=code)
            if instance and instance.pk:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                self.add_error('code', "This Supplier Code is already in use. It must be unique.")
                
        return cleaned_data
