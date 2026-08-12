from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register('operations', api_views.BarcodeAPIViewSet, basename='api-barcode-ops')
router.register('history', api_views.BarcodeScanHistoryViewSet, basename='api-scan-history')
router.register('sessions', api_views.ScanSessionViewSet, basename='api-scan-sessions')
router.register('presets', api_views.BarcodeLabelPresetViewSet, basename='api-label-presets')

urlpatterns = [
    # REST API ViewSets
    path('api/', include(router.urls)),

    # Web Controller Views
    path('scan/', views.BarcodeScannerView.as_view(), name='barcode-scanner'),
    path('generator/', views.BarcodeScannerView.as_view(), name='barcode-generator'),
    path('mobile/', views.MobileWarehouseScannerView.as_view(), name='mobile-scanner'),
    path('count/', views.StockCountingView.as_view(), name='stock-counting'),
    path('sessions/', views.ScanSessionsView.as_view(), name='scan-sessions'),
    path('generate/<int:product_id>/', views.BarcodeGeneratorView.as_view(), name='barcode-generator'),
    path('labels/', views.BarcodeLabelPrintView.as_view(), name='barcode-labels'),
    path('history/', views.BarcodeScanHistoryView.as_view(), name='barcode-history'),
]

