from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from products.models import Product, Warehouse
from .models import BarcodeScanHistory, BarcodeLabelPreset
from .serializers import BarcodeScanHistorySerializer, BarcodeLabelPresetSerializer
from .services import BarcodeService

class BarcodeAPIViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='lookup')
    def lookup_product(self, request):
        query = request.query_params.get('barcode') or request.query_params.get('q')
        scan_mode = request.query_params.get('mode', 'lookup')
        warehouse_id = request.query_params.get('warehouse_id')

        wh = Warehouse.objects.filter(id=warehouse_id).first() if warehouse_id else None
        res_data = BarcodeService.lookup_product(query)

        if res_data:
            prod = res_data['product']
            BarcodeService.log_scan_history(query, product=prod, user=request.user, warehouse=wh, scan_mode=scan_mode, status='found', request=request)
            return Response({
                'found': True,
                'product_id': prod.id,
                'product_name': prod.name,
                'sku': prod.sku,
                'barcode': prod.barcode or prod.sku,
                'category': prod.category.name if prod.category else 'N/A',
                'brand': prod.brand.name if prod.brand else 'N/A',
                'unit': prod.unit.name if prod.unit else 'N/A',
                'purchase_price': float(prod.purchase_price or 0),
                'selling_price': float(prod.selling_price or 0),
                'total_quantity': res_data['total_quantity'],
                'total_value': res_data['total_value'],
                'warehouse_stocks': res_data['warehouse_stocks'],
                'barcode_svg': res_data['barcode_svg'],
                'qr_svg': res_data['qr_svg']
            }, status=status.HTTP_200_OK)
        else:
            BarcodeService.log_scan_history(query or 'UNKNOWN', product=None, user=request.user, warehouse=wh, scan_mode=scan_mode, status='not_found', request=request)
            return Response({
                'found': False,
                'message': f"Product not found for barcode '{query}'."
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_barcode(self, request):
        product_id = request.data.get('product_id')
        prod = Product.objects.filter(id=product_id).first()
        if not prod:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not prod.barcode:
            prod.barcode = BarcodeService.generate_unique_barcode()
            prod.save()

        return Response({
            'product_id': prod.id,
            'product_name': prod.name,
            'barcode': prod.barcode,
            'barcode_svg': BarcodeService.render_barcode_svg(prod.barcode),
            'qr_svg': BarcodeService.render_qr_code_svg(prod)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='scan')
    def process_scan(self, request):
        barcode = request.data.get('barcode')
        mode = request.data.get('mode', 'lookup')
        warehouse_id = request.data.get('warehouse_id')
        qty = int(request.data.get('quantity', 1))

        wh = Warehouse.objects.filter(id=warehouse_id).first() if warehouse_id else None
        res = BarcodeService.process_scan_operation(user=request.user, warehouse=wh, scan_mode=mode, barcode_value=barcode, quantity=qty)
        return Response(res, status=status.HTTP_200_OK if res['status'] == 'success' else status.HTTP_400_BAD_REQUEST)

class BarcodeScanHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BarcodeScanHistory.objects.all()
    serializer_class = BarcodeScanHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

class ScanSessionViewSet(viewsets.ModelViewSet):
    from .models import ScanSession
    from .serializers import ScanSessionSerializer
    queryset = ScanSession.objects.prefetch_related('items').all()
    serializer_class = ScanSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

class BarcodeLabelPresetViewSet(viewsets.ModelViewSet):
    queryset = BarcodeLabelPreset.objects.all()
    serializer_class = BarcodeLabelPresetSerializer
    permission_classes = [permissions.IsAuthenticated]

