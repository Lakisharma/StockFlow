from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register('accounts', api_views.PaymentAccountViewSet, basename='api-account')
router.register('transactions', api_views.PaymentViewSet, basename='api-payment')

urlpatterns = [
    # REST API Router
    path('api/', include(router.urls)),

    # Finance Dashboard
    path('dashboard/', views.FinanceDashboardView.as_view(), name='finance-dashboard'),

    # Receivables & Payables
    path('receivables/', views.ReceivablesListView.as_view(), name='receivables-list'),
    path('payables/', views.PayablesListView.as_view(), name='payables-list'),

    # Transactions & Receipts
    path('transactions/', views.PaymentListView.as_view(), name='payment-list'),
    path('transactions/create/', views.PaymentCreateView.as_view(), name='payment-create'),
    path('transactions/<int:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('transactions/<int:pk>/reverse/', views.PaymentReverseView.as_view(), name='payment-reverse'),
    path('transactions/<int:pk>/print/', views.PaymentPrintView.as_view(), name='payment-print'),

    # Ledgers & Aging Analysis
    path('ledger/', views.CustomerLedgerView.as_view(), name='customer-ledger'),
    path('aging/', views.AgingReportView.as_view(), name='aging-report'),
]
