import random
from django import forms
from .models import Product, Warehouse
from categories.models import Category
from brands.models import Brand
from units.models import Unit

class ProductForm(forms.ModelForm):
    auto_generate_sku = forms.BooleanField(required=False, initial=False, label="Auto Generate SKU")
    auto_generate_barcode = forms.BooleanField(required=False, initial=False, label="Auto Generate Barcode")

    class Meta:
        model = Product
        fields = [
            # Basic Info
            'image', 'name', 'sku', 'barcode', 'category', 'brand', 'unit', 'description', 'status',
            # Pricing
            'purchase_price', 'selling_price', 'mrp', 'discount', 'gst_rate', 'tax_type',
            # Inventory
            'opening_stock', 'current_stock', 'min_stock_level', 'max_stock_level', 'warehouse', 'stock_alert',
            # Identification
            'hsn_code', 'product_code',
            # Additional Info
            'weight', 'dimensions', 'manufacturer', 'country_of_origin', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Product Name'}),
            'sku': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Unique SKU (e.g. ELE-00001)'}),
            'barcode': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Barcode number'}),
            'category': forms.Select(attrs={'class': 'input-control'}),
            'brand': forms.Select(attrs={'class': 'input-control'}),
            'unit': forms.Select(attrs={'class': 'input-control'}),
            'description': forms.Textarea(attrs={'class': 'input-control', 'rows': 3, 'placeholder': 'Description...'}),
            'status': forms.Select(attrs={'class': 'input-control'}),
            
            'purchase_price': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01', 'placeholder': '0.00'}),
            'selling_price': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01', 'placeholder': '0.00'}),
            'mrp': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01', 'placeholder': '0.00'}),
            'discount': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01', 'placeholder': '0.00'}),
            'gst_rate': forms.NumberInput(attrs={'class': 'input-control', 'step': '0.01', 'placeholder': '18.00'}),
            'tax_type': forms.Select(attrs={'class': 'input-control'}),
            
            'opening_stock': forms.NumberInput(attrs={'class': 'input-control', 'placeholder': '0'}),
            'current_stock': forms.NumberInput(attrs={'class': 'input-control', 'placeholder': '0'}),
            'min_stock_level': forms.NumberInput(attrs={'class': 'input-control', 'placeholder': '5'}),
            'max_stock_level': forms.NumberInput(attrs={'class': 'input-control', 'placeholder': '1000'}),
            'warehouse': forms.Select(attrs={'class': 'input-control'}),
            'stock_alert': forms.CheckboxInput(attrs={'style': 'cursor: pointer; width: 18px; height: 18px;'}),
            
            'hsn_code': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'HSN Code'}),
            'product_code': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Product Code'}),
            
            'weight': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'e.g. 1.2 kg'}),
            'dimensions': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'e.g. 10x15x5 cm'}),
            'manufacturer': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Manufacturer Name'}),
            'country_of_origin': forms.TextInput(attrs={'class': 'input-control', 'placeholder': 'Country name'}),
            'notes': forms.Textarea(attrs={'class': 'input-control', 'rows': 2, 'placeholder': 'Additional notes...'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Handle field classes and uploads
        self.fields['image'].widget.attrs.update({'class': 'input-control-file'})
        self.fields['sku'].required = False  # Required=False because it can be auto-generated

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Product Name is required.")
        return name

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        sku = cleaned_data.get('sku')
        auto_generate_sku = cleaned_data.get('auto_generate_sku')
        category = cleaned_data.get('category')
        
        # Validate prices
        purchase_price = cleaned_data.get('purchase_price')
        selling_price = cleaned_data.get('selling_price')
        if purchase_price is not None and selling_price is not None:
            if purchase_price < 0:
                self.add_error('purchase_price', "Purchase price cannot be negative.")
            if selling_price < 0:
                self.add_error('selling_price', "Selling price cannot be negative.")
        
        # Auto-generate SKU if selected or if SKU field is blank
        if auto_generate_sku or not sku:
            if not category:
                self.add_error('sku', "Category is required to auto-generate SKU.")
            else:
                prefix = (category.name[:3]).upper()
                # Find sequential number
                count = Product.objects.filter(sku__startswith=prefix).count() + 1
                new_sku = f"{prefix}-{count:05d}"
                # Handle race conditions/collisions
                while Product.objects.filter(sku=new_sku).exists():
                    count += 1
                    new_sku = f"{prefix}-{count:05d}"
                cleaned_data['sku'] = new_sku
        else:
            # Check unique SKU manually
            instance = self.instance
            qs = Product.objects.filter(sku__iexact=sku)
            if instance and instance.pk:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                self.add_error('sku', "This SKU is already in use. It must be unique.")
                
        # Auto-generate Barcode if selected or if barcode is blank
        barcode = cleaned_data.get('barcode')
        auto_generate_barcode = cleaned_data.get('auto_generate_barcode')
        if auto_generate_barcode or not barcode:
            # Generate a 12-digit random barcode number
            new_barcode = "".join([str(random.randint(0, 9)) for _ in range(12)])
            while Product.objects.filter(barcode=new_barcode).exists():
                new_barcode = "".join([str(random.randint(0, 9)) for _ in range(12)])
            cleaned_data['barcode'] = new_barcode
            
        return cleaned_data
