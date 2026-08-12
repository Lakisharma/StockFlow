from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from products.models import WarehouseStock
from .models import StockMovement, StockAdjustment
from .serializers import WarehouseStockSerializer, StockMovementSerializer, StockAdjustmentSerializer

class WarehouseStockViewSet(viewsets.ModelViewSet):
    queryset = WarehouseStock.objects.select_related('product', 'warehouse', 'product__category', 'product__brand', 'product__unit').all()
    serializer_class = WarehouseStockSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['product__name', 'product__sku', 'product__barcode', 'warehouse__name']
    ordering_fields = ['quantity', 'updated_at']

    def get_queryset(self):
        qs = super().get_queryset()
        wh = self.request.query_params.get('warehouse')
        if wh:
            qs = qs.filter(warehouse_id=wh)
        cat = self.request.query_params.get('category')
        if cat:
            qs = qs.filter(product__category_id=cat)
        return qs

class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related('product', 'warehouse', 'user').all()
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['product__name', 'product__sku', 'reference_number', 'reason', 'notes']
    ordering_fields = ['created_at', 'quantity']

    def get_queryset(self):
        qs = super().get_queryset()
        wh = self.request.query_params.get('warehouse')
        if wh:
            qs = qs.filter(warehouse_id=wh)
        ttype = self.request.query_params.get('transaction_type')
        if ttype:
            qs = qs.filter(transaction_type=ttype)
        return qs

class StockAdjustmentViewSet(viewsets.ModelViewSet):
    queryset = StockAdjustment.objects.select_related('product', 'warehouse', 'user').all()
    serializer_class = StockAdjustmentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['product__name', 'notes']
    ordering_fields = ['created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        wh = self.request.query_params.get('warehouse')
        if wh:
            qs = qs.filter(warehouse_id=wh)
        return qs
