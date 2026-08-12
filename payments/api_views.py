from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import PaymentAccount, Payment
from .serializers import PaymentAccountSerializer, PaymentSerializer
from .services import FinanceService

class PaymentAccountViewSet(viewsets.ModelViewSet):
    queryset = PaymentAccount.objects.all()
    serializer_class = PaymentAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['account_name', 'bank_name', 'account_number_masked']

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related('customer', 'supplier', 'account', 'sales_invoice', 'purchase').prefetch_related('allocations').all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['payment_number', 'reference_number', 'customer__name', 'supplier__name']
    ordering_fields = ['payment_date', 'amount', 'created_at']

    @action(detail=True, methods=['post'])
    def reverse(self, request, pk=None):
        payment = self.get_object()
        reason = request.data.get('reason', 'Payment reversal requested via API')
        FinanceService.reverse_payment(payment, request.user, reason)
        return Response({'message': f"Payment '{payment.payment_number}' reversed successfully."}, status=status.HTTP_200_OK)
