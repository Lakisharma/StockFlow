from django import forms
from .models import Brand

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'code', 'description', 'logo', 'website', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input-control',
                'placeholder': 'Enter brand name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'input-control',
                'placeholder': 'Enter unique brand code (e.g. NIKE)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'input-control',
                'rows': 4,
                'placeholder': 'Enter brand description...'
            }),
            'logo': forms.ClearableFileInput(attrs={
                'class': 'input-control-file'
            }),
            'website': forms.URLInput(attrs={
                'class': 'input-control',
                'placeholder': 'https://example.com'
            }),
            'status': forms.Select(attrs={
                'class': 'input-control'
            })
        }
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Brand Name is required.")
        return name

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code:
            raise forms.ValidationError("Brand Code is required.")
            
        # Check uniqueness manually
        instance = self.instance
        qs = Brand.objects.filter(code__iexact=code)
        if instance and instance.pk:
            qs = qs.exclude(pk=instance.pk)
            
        if qs.exists():
            raise forms.ValidationError("This Brand Code is already in use. It must be unique.")
            
        return code.upper() # Standardize brand codes as uppercase
