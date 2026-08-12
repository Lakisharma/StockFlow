from rest_framework import serializers
from products.models import Warehouse
from .models import WarehouseZone, WarehouseBin, WarehouseReorderSetting, WarehouseUserAccess

class WarehouseMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = [
            'id', 'name', 'code', 'warehouse_type', 'description', 'status',
            'manager_name', 'phone', 'email', 'address', 'city', 'state',
            'pin_code', 'total_capacity', 'capacity_unit', 'opening_date', 'operating_hours'
        ]

class WarehouseZoneSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = WarehouseZone
        fields = ['id', 'warehouse', 'warehouse_name', 'zone_code', 'zone_name', 'description', 'capacity', 'status', 'created_at']

class WarehouseBinSerializer(serializers.ModelSerializer):
    zone_code = serializers.CharField(source='zone.zone_code', read_only=True)
    warehouse_name = serializers.CharField(source='zone.warehouse.name', read_only=True)

    class Meta:
        model = WarehouseBin
        fields = ['id', 'zone', 'zone_code', 'warehouse_name', 'bin_code', 'rack', 'shelf', 'bin_number', 'capacity', 'status', 'created_at']

class WarehouseReorderSettingSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = WarehouseReorderSetting
        fields = ['id', 'warehouse', 'warehouse_name', 'product', 'product_name', 'minimum_stock', 'maximum_stock', 'reorder_level', 'reorder_quantity']
