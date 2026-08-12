from rest_framework import serializers

class DashboardMetricsSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_inventory_qty = serializers.IntegerField()
    total_inventory_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_purchases = serializers.IntegerField()
    total_purchase_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_suppliers = serializers.IntegerField()
    total_warehouses = serializers.IntegerField()
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()

class GSTReportSummarySerializer(serializers.Serializer):
    total_taxable = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_cgst = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_sgst = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_igst = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_gst = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_grand = serializers.DecimalField(max_digits=15, decimal_places=2)
