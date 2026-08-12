from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # REST API Endpoints
    path('api/metrics/', api_views.DashboardMetricsAPIView.as_view(), name='api-reports-metrics'),
    path('api/comparison/', api_views.WarehouseComparisonAPIView.as_view(), name='api-reports-comparison'),

    # Web View Routes
    path('', views.ReportDashboardView.as_view(), name='reports-dashboard'),
    path('inventory/', views.InventoryReportView.as_view(), name='report-inventory'),
    path('stock-movement/', views.StockMovementReportView.as_view(), name='report-stock-movement'),
    path('purchase/', views.PurchaseReportView.as_view(), name='report-purchase'),
    path('supplier/', views.SupplierReportView.as_view(), name='report-supplier'),
    path('warehouse/', views.WarehouseReportView.as_view(), name='report-warehouse'),
    path('low-stock/', views.LowStockReportView.as_view(), name='report-low-stock'),
    path('out-of-stock/', views.OutOfStockReportView.as_view(), name='report-out-of-stock'),
    path('product/', views.ProductReportView.as_view(), name='report-product'),
    path('stock-transfer/', views.StockTransferReportView.as_view(), name='report-stock-transfer'),
    path('gst/', views.GSTReportView.as_view(), name='report-gst'),
    path('profit-loss/', views.ReportDashboardView.as_view(), name='report-profit-loss'),
    path('valuation/', views.ValuationReportView.as_view(), name='report-valuation'),
    path('export/<str:report_type>/csv/', views.export_report_csv, name='report-export-csv'),
]
