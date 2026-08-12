from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Customer, SalesOrder, Dispatch, SalesInvoice
from .serializers import CustomerSerializer, SalesOrderSerializer, DispatchSerializer, SalesInvoiceSerializer
from .services import SalesService

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['customer_code', 'name', 'business_name', 'phone', 'gstin']
    ordering_fields = ['name', 'outstanding_amount', 'created_at']

class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.select_related('customer', 'warehouse').prefetch_related('items').all()
    serializer_class = SalesOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['so_number', 'customer__name', 'warehouse__name']
    ordering_fields = ['order_date', 'grand_total', 'created_at']

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        so = self.get_object()
        SalesService.submit_so_for_approval(so, request.user)
        return Response({'message': f"Sales Order '{so.so_number}' submitted for approval."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        so = self.get_object()
        SalesService.approve_so(so, request.user)
        return Response({'message': f"Sales Order '{so.so_number}' approved successfully."}, status=status.HTTP_200_OK)

class DispatchViewSet(viewsets.ModelViewSet):
    queryset = Dispatch.objects.select_related('customer', 'warehouse', 'sales_order').prefetch_related('items').all()
    serializer_class = DispatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['dispatch_number', 'customer__name', 'tracking_number']
    ordering_fields = ['dispatch_date', 'created_at']

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        dispatch = self.get_object()
        SalesService.confirm_dispatch(dispatch, request.user)
        return Response({'message': f"Dispatch '{dispatch.dispatch_number}' confirmed and inventory updated."}, status=status.HTTP_200_OK)

class SalesInvoiceViewSet(viewsets.ModelViewSet):
    queryset = SalesInvoice.objects.select_related('customer', 'warehouse', 'sales_order').all()
    serializer_class = SalesInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['invoice_number', 'customer__name']
    ordering_fields = ['invoice_date', 'grand_total', 'created_at']
