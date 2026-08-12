from rest_framework import serializers
from .models import CompanyProfile, TaxSettings, InvoiceSettings, CurrencySettings

class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = '__all__'

class TaxSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxSettings
        fields = '__all__'

class InvoiceSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceSettings
        fields = '__all__'

class CurrencySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencySettings
        fields = '__all__'
