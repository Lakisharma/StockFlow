from rest_framework import serializers
from .models import Customer, SalesOrder, SalesOrderItem, PickList, PickListItem, Dispatch, DispatchItem, SalesInvoice

class CustomerSerializer(serializers.ModelSerializer):
    available_credit = serializers.FloatField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'customer_code', 'name', 'business_name', 'phone',
            'alternate_phone', 'email', 'gstin', 'pan', 'billing_address',
            'shipping_address', 'city', 'state', 'pincode', 'payment_terms',
            'credit_limit', 'opening_balance', 'outstanding_amount',
            'available_credit', 'status', 'created_at'
        ]

class SalesOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = SalesOrderItem
        fields = [
            'id', 'product', 'product_name', 'sku', 'ordered_quantity',
            'picked_quantity', 'dispatched_quantity', 'rate', 'discount_percent',
            'gst_percent', 'line_total'
        ]

class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = SalesOrder
        fields = [
            'id', 'so_number', 'customer', 'customer_name', 'warehouse', 'warehouse_name',
            'order_date', 'expected_dispatch_date', 'payment_terms', 'shipping_address',
            'billing_address', 'subtotal', 'discount_amount', 'tax_amount', 'shipping_charges',
            'grand_total', 'notes', 'status', 'items', 'created_at', 'updated_at'
        ]

class DispatchItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = DispatchItem
        fields = ['id', 'product', 'product_name', 'dispatched_quantity', 'batch_number', 'serial_numbers', 'rate', 'line_total']

class DispatchSerializer(serializers.ModelSerializer):
    items = DispatchItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = Dispatch
        fields = [
            'id', 'dispatch_number', 'sales_order', 'customer', 'customer_name',
            'warehouse', 'warehouse_name', 'dispatch_date', 'transporter',
            'vehicle_number', 'tracking_number', 'driver_name', 'driver_phone',
            'status', 'items', 'created_at', 'confirmed_at'
        ]

class SalesInvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = SalesInvoice
        fields = [
            'id', 'invoice_number', 'sales_order', 'dispatch', 'customer',
            'customer_name', 'warehouse', 'invoice_date', 'subtotal',
            'discount_amount', 'tax_amount', 'shipping_charges', 'grand_total',
            'paid_amount', 'status', 'payment_status', 'created_at'
        ]
