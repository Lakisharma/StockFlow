from rest_framework import serializers
from products.models import WarehouseStock, Product, Warehouse
from .models import StockMovement, StockAdjustment

class WarehouseStockSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')
    product_barcode = serializers.ReadOnlyField(source='product.barcode')
    category_name = serializers.ReadOnlyField(source='product.category.name')
    brand_name = serializers.ReadOnlyField(source='product.brand.name', default='N/A')
    unit_name = serializers.ReadOnlyField(source='product.unit.name')
    warehouse_name = serializers.ReadOnlyField(source='warehouse.name')
    stock_status = serializers.ReadOnlyField()
    inventory_value = serializers.ReadOnlyField()

    class Meta:
        model = WarehouseStock
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'product_barcode',
            'category_name', 'brand_name', 'unit_name', 'warehouse', 'warehouse_name',
            'quantity', 'min_stock_level', 'max_stock_level', 'rack_location',
            'batch_number', 'expiry_date', 'stock_status', 'inventory_value',
            'created_at', 'updated_at'
        ]

class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')
    warehouse_name = serializers.ReadOnlyField(source='warehouse.name')
    user_name = serializers.ReadOnlyField(source='user.username', default='System')
    transaction_type_display = serializers.ReadOnlyField(source='get_transaction_type_display')

    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'warehouse', 'warehouse_name',
            'transaction_type', 'transaction_type_display', 'quantity', 'previous_stock',
            'new_stock', 'unit_cost', 'reference_number', 'reason', 'notes', 'user_name',
            'created_at'
        ]

class StockAdjustmentSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    warehouse_name = serializers.ReadOnlyField(source='warehouse.name')
    user_name = serializers.ReadOnlyField(source='user.username', default='System')

    class Meta:
        model = StockAdjustment
        fields = [
            'id', 'product', 'product_name', 'warehouse', 'warehouse_name',
            'current_stock', 'physical_stock', 'difference_quantity', 'reason',
            'notes', 'user_name', 'created_at'
        ]
