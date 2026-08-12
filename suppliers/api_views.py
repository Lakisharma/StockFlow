from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Supplier, SupplierHistory
from .serializers import SupplierSerializer, SupplierHistorySerializer

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'company_name', 'contact_person', 'phone', 'email', 'gstin']
    ordering_fields = ['name', 'code', 'company_name', 'outstanding_balance', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        status = self.request.query_params.get('status')
        if status in ['active', 'inactive']:
            queryset = queryset.filter(status=status)
            
        payment_status = self.request.query_params.get('payment_status')
        if payment_status == 'overdue':
            # Simulated overdue condition (outstanding balance > credit limit or balance > 0 and past due days)
            queryset = queryset.filter(outstanding_balance__gt=0)
        elif payment_status == 'pending':
            queryset = queryset.filter(outstanding_balance__gt=0)
        elif payment_status == 'paid':
            queryset = queryset.filter(outstanding_balance__lte=0)
            
        return queryset

    def perform_create(self, serializer):
        supplier = serializer.save()
        SupplierHistory.objects.create(
            supplier=supplier,
            action="created",
            detail=f"Supplier profile '{supplier.name}' was created with code '{supplier.code}'."
        )

    def perform_update(self, serializer):
        old_supplier = self.get_object()
        old_outstanding = old_supplier.outstanding_balance
        
        supplier = serializer.save()
        
        details = []
        if old_outstanding != supplier.outstanding_balance:
            details.append(f"Outstanding balance changed from {old_outstanding} to {supplier.outstanding_balance}.")
            
        SupplierHistory.objects.create(
            supplier=supplier,
            action="updated",
            detail=f"Supplier details updated. {'; '.join(details)}"
        )

class SupplierHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SupplierHistory.objects.all()
    serializer_class = SupplierHistorySerializer
    filter_backends = [OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        supplier_id = self.request.query_params.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        return queryset
