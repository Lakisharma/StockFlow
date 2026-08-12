from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import OCRScan
from .serializers import OCRScanSerializer

class OCRScanViewSet(viewsets.ModelViewSet):
    queryset = OCRScan.objects.select_related('matched_supplier', 'warehouse', 'created_purchase', 'user').prefetch_related('items', 'audits').all()
    serializer_class = OCRScanSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['scan_id', 'original_filename', 'invoice_number', 'supplier_raw_name', 'matched_supplier__name']
    ordering_fields = ['created_at', 'overall_confidence', 'status']

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs
