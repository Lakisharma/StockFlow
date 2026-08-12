from rest_framework import serializers
from .models import (
    Purchase, PurchaseItem, PurchasePayment, 
    PurchaseOrder, PurchaseOrderItem, 
    PurchaseReturn, PurchaseReturnItem,
    GoodsReceiptNote, GRNItem
)
from suppliers.serializers import SupplierSerializer
from products.serializers import ProductSerializer, WarehouseSerializer

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'product', 'product_name', 'sku', 'quantity', 'rate', 'gst_percent', 'total_amount']

class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    supplier_detail = SupplierSerializer(source='supplier', read_only=True)
    warehouse_detail = WarehouseSerializer(source='warehouse', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier', 'supplier_detail', 'warehouse', 'warehouse_detail',
            'order_date', 'expected_delivery_date', 'payment_terms', 'terms_conditions',
            'subtotal', 'discount_amount', 'tax_amount', 'grand_total', 'notes',
            'approval_notes', 'status', 'items', 'created_by', 'approved_by', 'created_at', 'updated_at'
        ]

class GRNItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = GRNItem
        fields = [
            'id', 'grn', 'po_item', 'product', 'product_name', 'sku',
            'ordered_quantity', 'received_quantity', 'accepted_quantity',
            'rejected_quantity', 'short_quantity', 'damaged_quantity',
            'batch_number', 'mfg_date', 'expiry_date', 'serial_numbers',
            'rate', 'tax_amount', 'line_total'
        ]

class GoodsReceiptNoteSerializer(serializers.ModelSerializer):
    items = GRNItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True, default='N/A')

    class Meta:
        model = GoodsReceiptNote
        fields = [
            'id', 'grn_number', 'purchase_order', 'po_number', 'warehouse', 'warehouse_name',
            'supplier', 'supplier_name', 'received_date', 'challan_number', 'invoice_number',
            'status', 'quality_status', 'inspection_notes', 'items', 'inspected_by',
            'created_by', 'created_at', 'confirmed_at'
        ]

class PurchaseItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = PurchaseItem
        fields = [
            'id', 'product', 'product_detail', 'quantity', 'free_quantity', 'rate',
            'discount_percent', 'discount_amount', 'gst_percent', 'gst_amount',
            'taxable_amount', 'total_amount'
        ]

class PurchasePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchasePayment
        fields = ['id', 'purchase', 'amount', 'payment_date', 'payment_method', 'reference_number', 'notes', 'status', 'created_at']

class PurchaseReturnItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = PurchaseReturnItem
        fields = ['id', 'product', 'product_detail', 'return_quantity', 'refund_amount']

class PurchaseReturnSerializer(serializers.ModelSerializer):
    items = PurchaseReturnItemSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseReturn
        fields = ['id', 'return_number', 'purchase', 'return_date', 'warehouse', 'reason', 'total_return_amount', 'status', 'items', 'created_at']
