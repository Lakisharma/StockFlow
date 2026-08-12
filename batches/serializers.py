from rest_framework import serializers
from .models import ProductBatch, ProductSerialNumber

class ProductBatchSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    sku = serializers.CharField(source='product.sku', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, default='N/A')
    expiry_status = serializers.CharField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    inventory_value = serializers.FloatField(read_only=True)

    class Meta:
        model = ProductBatch
        fields = [
            'id', 'batch_number', 'product', 'product_name', 'sku',
            'warehouse', 'warehouse_name', 'supplier', 'supplier_name',
            'purchase_invoice', 'mfg_date', 'expiry_date', 'initial_quantity',
            'available_quantity', 'purchase_price', 'selling_price', 'status',
            'expiry_status', 'days_until_expiry', 'inventory_value', 'created_at'
        ]

class ProductSerialNumberSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    sku = serializers.CharField(source='product.sku', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True, default='N/A')
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True, default='N/A')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    warranty_status = serializers.CharField(read_only=True)

    class Meta:
        model = ProductSerialNumber
        fields = [
            'id', 'serial_number', 'product', 'product_name', 'sku',
            'batch', 'batch_number', 'warehouse', 'warehouse_name',
            'supplier', 'purchase_invoice', 'purchase_date',
            'warranty_start', 'warranty_end', 'status', 'status_display',
            'warranty_status', 'created_at'
        ]
