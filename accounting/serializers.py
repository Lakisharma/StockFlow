from rest_framework import serializers
from .models import ExpenseCategory, Expense, FinancialPeriod

class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name', 'code', 'description', 'status', 'created_at']

class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    account_name = serializers.CharField(source='account.account_name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'expense_number', 'expense_date', 'category', 'category_name',
            'description', 'amount', 'tax_amount', 'payment_method', 'account',
            'account_name', 'warehouse', 'warehouse_name', 'reference_number',
            'notes', 'status', 'created_by', 'created_at'
        ]

class FinancialPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialPeriod
        fields = ['id', 'period_name', 'start_date', 'end_date', 'is_locked', 'created_at']
