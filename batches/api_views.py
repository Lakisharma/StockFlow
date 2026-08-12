from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from products.models import Product, Warehouse
from .models import ProductBatch, ProductSerialNumber
from .serializers import ProductBatchSerializer, ProductSerialNumberSerializer
from .services import BatchService

class ProductBatchViewSet(viewsets.ModelViewSet):
    queryset = ProductBatch.objects.select_related('product', 'warehouse', 'supplier').all()
    serializer_class = ProductBatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='fefo-suggest')
    def fefo_suggest(self, request):
        product_id = request.query_params.get('product_id')
        warehouse_id = request.query_params.get('warehouse_id')
        qty = int(request.query_params.get('quantity', 1))

        prod = Product.objects.filter(id=product_id).first()
        wh = Warehouse.objects.filter(id=warehouse_id).first()

        if not prod or not wh:
            return Response({'error': 'Valid product_id and warehouse_id required.'}, status=status.HTTP_400_BAD_REQUEST)

        res = BatchService.get_fefo_batches(prod, wh, qty)
        allocations_serialized = []
        for item in res['allocations']:
            allocations_serialized.append({
                'batch_id': item['batch'].id,
                'batch_number': item['batch_number'],
                'expiry_date': item['expiry_date'],
                'take_quantity': item['take_quantity'],
                'available_quantity': item['available_quantity']
            })

        return Response({
            'product_name': prod.name,
            'warehouse_name': wh.name,
            'requested_quantity': qty,
            'is_fully_allocated': res['is_fully_allocated'],
            'unallocated_quantity': res['unallocated_quantity'],
            'allocations': allocations_serialized
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='dispatch-alerts')
    def dispatch_alerts(self, request):
        count = BatchService.dispatch_expiry_alerts()
        return Response({'message': f'Dispatched {count} batch expiry alert notifications.'}, status=status.HTTP_200_OK)

class ProductSerialNumberViewSet(viewsets.ModelViewSet):
    queryset = ProductSerialNumber.objects.select_related('product', 'batch', 'warehouse', 'supplier').all()
    serializer_class = ProductSerialNumberSerializer
    permission_classes = [permissions.IsAuthenticated]
