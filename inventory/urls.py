from django.urls import path
from . import views

urlpatterns = [
    path('', views.StockBalanceSummaryView.as_view(), name='inventory-list'),
    path('ledger/', views.UnifiedStockLedgerView.as_view(), name='stock-ledger'),
    path('balances/', views.StockBalanceSummaryView.as_view(), name='stock-balances'),
    path('workflow/', views.WorkflowStatusCenterView.as_view(), name='workflow-status'),
    path('detail/<int:pk>/', views.StockBalanceSummaryView.as_view(), name='inventory-detail'),
    path('adjustment/', views.UnifiedStockLedgerView.as_view(), name='stock-adjustment'),
]
