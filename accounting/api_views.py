from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import ExpenseCategory, Expense, FinancialPeriod
from .serializers import ExpenseCategorySerializer, ExpenseSerializer, FinancialPeriodSerializer
from .services import AccountingService

class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.select_related('category', 'account', 'warehouse', 'created_by').all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['expense_number', 'description', 'reference_number', 'category__name']
    ordering_fields = ['expense_date', 'amount', 'created_at']

class AccountingReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        data = AccountingService.get_financial_dashboard_data()
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def profit_loss(self, request):
        data = AccountingService.get_financial_dashboard_data()
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def cash_flow(self, request):
        data = AccountingService.get_cash_flow()
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def tax_summary(self, request):
        data = AccountingService.get_tax_summary()
        return Response(data, status=status.HTTP_200_OK)
