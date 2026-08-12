from rest_framework import serializers
from .models import StockTransfer, StockTransferItem, StockTransferHistory

class StockTransferItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')
    unit_name = serializers.ReadOnlyField(source='product.unit.short_name', default='PCS')

    class Meta:
        model = StockTransferItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'unit_name',
            'available_stock_snapshot', 'requested_quantity',
            'transferred_quantity', 'received_quantity', 'difference_quantity', 'remarks'
        ]

class StockTransferHistorySerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username', default='System')

    class Meta:
        model = StockTransferHistory
        fields = ['id', 'action', 'user_name', 'notes', 'created_at']

class StockTransferSerializer(serializers.ModelSerializer):
    from_warehouse_name = serializers.ReadOnlyField(source='from_warehouse.name')
    to_warehouse_name = serializers.ReadOnlyField(source='to_warehouse.name')
    requested_by_name = serializers.ReadOnlyField(source='requested_by.username', default='')
    approved_by_name = serializers.ReadOnlyField(source='approved_by.username', default='')
    received_by_name = serializers.ReadOnlyField(source='received_by.username', default='')
    items = StockTransferItemSerializer(many=True, read_only=True)
    history = StockTransferHistorySerializer(many=True, read_only=True)

    class Meta:
        model = StockTransfer
        fields = [
            'id', 'transfer_number', 'from_warehouse', 'from_warehouse_name',
            'to_warehouse', 'to_warehouse_name', 'transfer_date', 'expected_arrival_date',
            'priority', 'status', 'total_products', 'total_quantity', 'notes',
            'rejection_reason', 'requested_by_name', 'approved_by_name', 'received_by_name',
            'items', 'history', 'created_at', 'updated_at'
        ]
