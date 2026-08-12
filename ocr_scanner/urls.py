from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register(r'scans', api_views.OCRScanViewSet, basename='api-ocr-scan')

urlpatterns = [
    # REST API
    path('api/', include(router.urls)),

    # Web Views
    path('', views.ocr_upload, name='ocr-upload'),
    path('scan/', views.ocr_upload, name='ocr-scan'),
    path('upload/', views.ocr_upload, name='ocr-upload-alias'),
    path('verify/<int:pk>/', views.ocr_verify, name='ocr-verify'),
    path('convert/<int:pk>/', views.ocr_convert_to_purchase, name='ocr-convert'),
    path('history/', views.OCRHistoryListView.as_view(), name='ocr-history'),
    path('scan/<int:pk>/', views.OCRScanDetailView.as_view(), name='ocr-detail'),
    path('export/csv/', views.export_ocr_scans_csv, name='ocr-export-csv'),
]
