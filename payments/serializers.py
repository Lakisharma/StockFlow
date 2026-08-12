from rest_framework import serializers
from .models import PaymentAccount, Payment, PaymentAllocation

class PaymentAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAccount
        fields = ['id', 'account_name', 'account_type', 'bank_name', 'account_number_masked', 'ifsc_code', 'opening_balance', 'current_balance', 'status', 'created_at']

class PaymentAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAllocation
        fields = ['id', 'sales_invoice', 'purchase', 'allocated_amount', 'created_at']

class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    account_name = serializers.CharField(source='account.account_name', read_only=True)
    allocations = PaymentAllocationSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'payment_date', 'payment_type', 'customer',
            'customer_name', 'supplier', 'supplier_name', 'sales_invoice',
            'purchase', 'amount', 'payment_method', 'reference_number',
            'account', 'account_name', 'notes', 'status', 'reversal_reason',
            'allocations', 'created_at'
        ]
