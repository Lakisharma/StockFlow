from rest_framework import serializers
from .models import OCRScan, OCRScanItem, OCRScanAudit

class OCRScanItemSerializer(serializers.ModelSerializer):
    matched_product_name = serializers.ReadOnlyField(source='matched_product.name', default='')
    matched_product_sku = serializers.ReadOnlyField(source='matched_product.sku', default='')

    class Meta:
        model = OCRScanItem
        fields = [
            'id', 'raw_product_name', 'matched_product', 'matched_product_name',
            'matched_product_sku', 'hsn_code', 'batch_number', 'expiry_date',
            'quantity', 'free_quantity', 'unit_name', 'rate', 'discount_percent',
            'gst_percent', 'taxable_amount', 'total_amount', 'confidence_score'
        ]

class OCRScanAuditSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username', default='System')

    class Meta:
        model = OCRScanAudit
        fields = ['id', 'action', 'user_name', 'field_name', 'old_value', 'new_value', 'created_at']

class OCRScanSerializer(serializers.ModelSerializer):
    matched_supplier_name = serializers.ReadOnlyField(source='matched_supplier.name', default='')
    warehouse_name = serializers.ReadOnlyField(source='warehouse.name', default='')
    created_by_username = serializers.ReadOnlyField(source='user.username', default='')
    items = OCRScanItemSerializer(many=True, read_only=True)
    audits = OCRScanAuditSerializer(many=True, read_only=True)

    class Meta:
        model = OCRScan
        fields = [
            'id', 'scan_id', 'document', 'original_filename', 'file_type', 'file_size',
            'status', 'overall_confidence', 'raw_extracted_text', 'invoice_number',
            'invoice_date', 'po_number', 'supplier_raw_name', 'supplier_gstin',
            'matched_supplier', 'matched_supplier_name', 'subtotal', 'tax_amount',
            'discount_amount', 'grand_total', 'warehouse', 'warehouse_name',
            'created_purchase', 'created_by_username', 'processing_time_seconds',
            'items', 'audits', 'created_at', 'updated_at'
        ]
