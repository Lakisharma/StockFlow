import re
from django import forms
from .models import Warehouse

class WarehouseForm(forms.ModelForm):
    auto_generate_code = forms.BooleanField(required=False, initial=False, label="Auto Generate Warehouse Code")

    class Meta:
        model = Warehouse
        fields = [
            # Basic Info
            'name', 'code', 'warehouse_type', 'description', 'status', 'logo',
            # Contact Info
            'manager_name', 'phone', 'alternate_phone', 'email',
            # Address
            'address', 'city', 'state', 'country', 'pin_code',
            # Capacity
            'total_capacity', 'capacity_unit',
            # Additional Information
            'opening_date', 'operating_hours', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Warehouse Name'}),
            'code': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Unique Code (e.g. WH-00001)'}),
            'warehouse_type': forms.Select(attrs={'class': 'input-control'}),
            'description': forms.Textarea(attrs={'class': 'input-control', 'rows': 3, 'placeholder': 'Description...'}),
            'status': forms.Select(attrs={'class': 'input-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'input-control-file'}),
            
            'manager_name': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Manager Name'}),
            'phone': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Phone Number'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Alternate Phone'}),
            'email': forms.EmailInput(attrs={'class': 'input-control', 'placeholder': 'Email Address'}),
            
            'address': forms.Textarea(attrs={'class': 'input-control', 'rows': 2, 'placeholder': 'Full Address...'}),
            'city': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'State'}),
            'country': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Country'}),
            'pin_code': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'PIN / ZIP Code'}),
            
            'total_capacity': forms.NumberInput(attrs={'class': 'input-control', 'placeholder': '10000'}),
            'capacity_unit': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'e.g. Sq Ft, Boxes, Units'}),
            
            'opening_date': forms.DateInput(attrs={'class': 'input-control', 'type': 'date'}),
            'operating_hours': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'e.g. 09:00 - 18:00'}),
            'notes': forms.Textarea(attrs={'class': 'input-control', 'rows': 2, 'placeholder': 'Notes...'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].required = False  # Required=False because it can be auto-generated

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not re.match(r'^\+?[0-9\s\-]+$', phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_pin_code(self):
        pin_code = self.cleaned_data.get('pin_code')
        if pin_code and not re.match(r'^[a-zA-Z0-9\s\-]+$', pin_code):
            raise forms.ValidationError("Enter a valid PIN / ZIP code.")
        return pin_code

    def clean_total_capacity(self):
        capacity = self.cleaned_data.get('total_capacity')
        if capacity is not None and capacity <= 0:
            raise forms.ValidationError("Capacity must be a positive integer.")
        return capacity

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        auto_generate_code = cleaned_data.get('auto_generate_code')
        
        # Auto-generate code if requested or empty
        if auto_generate_code or not code:
            prefix = "WH"
            count = Warehouse.objects.count() + 1
            new_code = f"{prefix}-{count:05d}"
            while Warehouse.objects.filter(code=new_code).exists():
                count += 1
                new_code = f"{prefix}-{count:05d}"
            cleaned_data['code'] = new_code
        else:
            # Unique validation check
            instance = self.instance
            qs = Warehouse.objects.filter(code__iexact=code)
            if instance and instance.pk:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                self.add_error('code', "This Warehouse Code is already in use. It must be unique.")
                
        return cleaned_data
