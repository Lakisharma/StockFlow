from rest_framework import serializers
from .models import Supplier, SupplierHistory

class SupplierHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierHistory
        fields = ['id', 'supplier', 'action', 'detail', 'created_at']

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'code', 'company_name', 'contact_person', 'supplier_type', 'status', 'logo',
            'phone', 'alternate_phone', 'email', 'website',
            'address', 'city', 'state', 'country', 'pin_code',
            'gstin', 'pan', 'tax_reg_type',
            'bank_name', 'holder_name', 'account_number', 'ifsc_code', 'branch',
            'payment_terms', 'credit_limit', 'opening_balance', 'outstanding_balance', 'due_days',
            'notes', 'internal_remarks', 'created_at', 'updated_at'
        ]
