from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from .models import Purchase, PurchaseOrder, PurchasePayment, PurchaseReturn, GoodsReceiptNote, GRNItem
from .serializers import (
    PurchaseOrderSerializer, 
    PurchasePaymentSerializer, PurchaseReturnSerializer,
    GoodsReceiptNoteSerializer, GRNItemSerializer
)
from .services import ProcurementService

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related('supplier', 'warehouse').prefetch_related('items').all()
    serializer_class = PurchaseOrderSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['po_number', 'supplier__name', 'warehouse__name']
    ordering_fields = ['order_date', 'grand_total', 'created_at']

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        po = self.get_object()
        ProcurementService.submit_po_for_approval(po, request.user)
        return Response({'message': f"PO '{po.po_number}' submitted for approval."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        po = self.get_object()
        notes = request.data.get('notes', '')
        ProcurementService.approve_po(po, request.user, notes=notes)
        return Response({'message': f"PO '{po.po_number}' approved successfully."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        po = self.get_object()
        notes = request.data.get('notes', '')
        ProcurementService.reject_po(po, request.user, notes=notes)
        return Response({'message': f"PO '{po.po_number}' rejected."}, status=status.HTTP_200_OK)

class GoodsReceiptNoteViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceiptNote.objects.select_related('supplier', 'warehouse', 'purchase_order').prefetch_related('items').all()
    serializer_class = GoodsReceiptNoteSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['grn_number', 'supplier__name', 'warehouse__name', 'purchase_order__po_number']
    ordering_fields = ['received_date', 'created_at']

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        grn = self.get_object()
        ProcurementService.confirm_grn(grn, request.user)
        return Response({'message': f"GRN '{grn.grn_number}' confirmed and warehouse stock updated."}, status=status.HTTP_200_OK)

class PurchasePaymentViewSet(viewsets.ModelViewSet):
    queryset = PurchasePayment.objects.all()
    serializer_class = PurchasePaymentSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['reference_number', 'purchase__invoice_number']
    ordering_fields = ['payment_date', 'amount', 'created_at']

class PurchaseReturnViewSet(viewsets.ModelViewSet):
    queryset = PurchaseReturn.objects.all()
    serializer_class = PurchaseReturnSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['return_number', 'purchase__invoice_number']
    ordering_fields = ['return_date', 'created_at']
