from rest_framework import serializers
from .models import BarcodeScanHistory, BarcodeLabelPreset, ScanSession, ScanSessionItem

class BarcodeScanHistorySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    scan_mode_display = serializers.CharField(source='get_scan_mode_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = BarcodeScanHistory
        fields = [
            'id', 'scan_id', 'barcode_value', 'product', 'product_name',
            'user', 'username', 'warehouse', 'warehouse_name', 'scan_mode',
            'scan_mode_display', 'status', 'status_display', 'quantity', 'timestamp'
        ]

class BarcodeLabelPresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarcodeLabelPreset
        fields = '__all__'

class ScanSessionItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ScanSessionItem
        fields = ['id', 'session', 'barcode_value', 'product', 'product_name', 'quantity', 'status', 'message', 'scanned_at']

class ScanSessionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    items = ScanSessionItemSerializer(many=True, read_only=True)

    class Meta:
        model = ScanSession
        fields = ['id', 'session_number', 'user', 'username', 'warehouse', 'warehouse_name', 'scan_mode', 'start_time', 'end_time', 'total_scans', 'successful_scans', 'failed_scans', 'status', 'items']

