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

from categories.models import Category
from units.models import Unit

class ProductSerializer(serializers.ModelSerializer):
    stock_status = serializers.ReadOnlyField()
    category_detail = CategorySerializer(source='category', read_only=True)
    brand_detail = BrandSerializer(source='brand', read_only=True)
    unit_detail = UnitSerializer(source='unit', read_only=True)
    warehouse_detail = WarehouseSerializer(source='warehouse', read_only=True)
    
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all(), required=False, allow_null=True)

    def validate_category(self, value):
        if not value:
            cat = Category.objects.filter(status='active').first() or Category.objects.first()
            if not cat:
                cat = Category.objects.create(name='General', code='CAT-GEN', status='active')
            return cat
        return value

    def validate_unit(self, value):
        if not value:
            u = Unit.objects.filter(status='active').first() or Unit.objects.first()
            if not u:
                u = Unit.objects.create(name='Piece', short_name='PCS', status='active')
            return u
        return value

    def create(self, validated_data):
        if 'category' not in validated_data or not validated_data['category']:
            cat = Category.objects.filter(status='active').first() or Category.objects.first()
            if not cat:
                cat = Category.objects.create(name='General', code='CAT-GEN', status='active')
            validated_data['category'] = cat

        if 'unit' not in validated_data or not validated_data['unit']:
            u = Unit.objects.filter(status='active').first() or Unit.objects.first()
            if not u:
                u = Unit.objects.create(name='Piece', short_name='PCS', status='active')
            validated_data['unit'] = u

        return super().create(validated_data)

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

