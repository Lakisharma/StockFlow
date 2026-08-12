from django import forms
from .models import Unit

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'short_name', 'description', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input-control',
                'placeholder': 'Enter unit name (e.g. Kilogram)'
            }),
            'short_name': forms.TextInput(attrs={
                'class': 'input-control',
                'placeholder': 'Enter unique short name (e.g. KG)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'input-control',
                'rows': 4,
                'placeholder': 'Enter unit description...'
            }),
            'status': forms.Select(attrs={
                'class': 'input-control'
            })
        }
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Unit Name is required.")
        return name

    def clean_short_name(self):
        short_name = self.cleaned_data.get('short_name')
        if not short_name:
            raise forms.ValidationError("Short Name is required.")
            
        # Check uniqueness manually
        instance = self.instance
        qs = Unit.objects.filter(short_name__iexact=short_name)
        if instance and instance.pk:
            qs = qs.exclude(pk=instance.pk)
            
        if qs.exists():
            raise forms.ValidationError("This Short Name is already in use. It must be unique.")
            
        return short_name.upper() # Standardize short names as uppercase
