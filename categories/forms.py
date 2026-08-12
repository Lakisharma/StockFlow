from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'code', 'description', 'image', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input-control',
                'placeholder': 'Enter category name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'input-control',
                'placeholder': 'Enter unique category code (e.g. CAT-001)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'input-control',
                'rows': 4,
                'placeholder': 'Enter category description...'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'input-control-file'
            }),
            'status': forms.Select(attrs={
                'class': 'input-control'
            })
        }
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Category Name is required.")
        return name

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code:
            raise forms.ValidationError("Category Code is required.")
        
        # Check uniqueness manually to ensure exact custom error message matches requirements
        instance = self.instance
        qs = Category.objects.filter(code__iexact=code)
        if instance and instance.pk:
            qs = qs.exclude(pk=instance.pk)
            
        if qs.exists():
            raise forms.ValidationError("This Category Code is already in use. It must be unique.")
            
        return code.upper() # Standardize codes as uppercase
