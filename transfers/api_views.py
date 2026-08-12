from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import StockTransfer
from .serializers import StockTransferSerializer

class StockTransferViewSet(viewsets.ModelViewSet):
    queryset = StockTransfer.objects.select_related(
        'from_warehouse', 'to_warehouse', 'requested_by', 'approved_by', 'received_by'
    ).prefetch_related('items', 'items__product', 'history').all()
    serializer_class = StockTransferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        'transfer_number', 'from_warehouse__name', 'to_warehouse__name',
        'items__product__name', 'items__product__sku'
    ]
    ordering_fields = ['transfer_date', 'status', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        from_wh = self.request.query_params.get('from_warehouse')
        if from_wh:
            qs = qs.filter(from_warehouse_id=from_wh)
        to_wh = self.request.query_params.get('to_warehouse')
        if to_wh:
            qs = qs.filter(to_warehouse_id=to_wh)
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs
