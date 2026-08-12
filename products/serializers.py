from rest_framework import serializers
from .models import Product, Warehouse, ProductHistory, WarehouseStock, WarehouseHistory
from categories.serializers import CategorySerializer
from brands.serializers import BrandSerializer
from units.serializers import UnitSerializer

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = [
            'id', 'name', 'code', 'warehouse_type', 'description', 'status', 'logo',
            'manager_name', 'phone', 'alternate_phone', 'email',
            'address', 'city', 'state', 'country', 'pin_code',
            'total_capacity', 'capacity_unit', 'opening_date', 'operating_hours', 'notes',
            'created_at', 'updated_at'
        ]

class WarehouseStockSerializer(serializers.ModelSerializer):
    stock_status = serializers.ReadOnlyField()
    class Meta:
        model = WarehouseStock
        fields = ['id', 'product', 'warehouse', 'quantity', 'min_stock_level', 'stock_status', 'created_at', 'updated_at']

class WarehouseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseHistory
        fields = ['id', 'warehouse', 'action', 'detail', 'created_at']

class ProductHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductHistory
        fields = ['id', 'product', 'action', 'detail', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    stock_status = serializers.ReadOnlyField()
    category_detail = CategorySerializer(source='category', read_only=True)
    brand_detail = BrandSerializer(source='brand', read_only=True)
    unit_detail = UnitSerializer(source='unit', read_only=True)
    warehouse_detail = WarehouseSerializer(source='warehouse', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'image', 'name', 'sku', 'barcode', 'qr_code', 
            'category', 'category_detail', 'brand', 'brand_detail', 
            'unit', 'unit_detail', 'description', 'status',
            'purchase_price', 'selling_price', 'mrp', 'discount', 
            'gst_rate', 'tax_type', 'opening_stock', 'current_stock', 
            'min_stock_level', 'max_stock_level', 'warehouse', 
            'warehouse_detail', 'stock_alert', 'hsn_code', 'product_code', 
            'weight', 'dimensions', 'manufacturer', 'country_of_origin', 
            'notes', 'stock_status', 'created_at', 'updated_at'
        ]
