from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register('categories', api_views.ExpenseCategoryViewSet, basename='api-expense-cat')
router.register('expenses', api_views.ExpenseViewSet, basename='api-expense')
router.register('reports', api_views.AccountingReportViewSet, basename='api-accounting-report')

urlpatterns = [
    # REST API Router
    path('api/', include(router.urls)),

    # Accounting Dashboard
    path('dashboard/', views.AccountingDashboardView.as_view(), name='accounting-dashboard'),

    # Financial Statements
    path('profit-loss/', views.ProfitAndLossView.as_view(), name='profit-loss'),
    path('cash-flow/', views.CashFlowView.as_view(), name='cash-flow'),
    path('tax-summary/', views.TaxSummaryView.as_view(), name='tax-summary'),
    path('inventory-valuation/', views.InventoryValuationView.as_view(), name='inventory-valuation'),

    # Expense Management
    path('expenses/', views.ExpenseListView.as_view(), name='expense-list'),
    path('expenses/create/', views.ExpenseCreateView.as_view(), name='expense-create'),

    # Profitability Reports
    path('profitability/products/', views.ProductProfitabilityView.as_view(), name='product-profitability'),
]
