from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register(r'transfers', api_views.StockTransferViewSet, basename='api-transfer')

urlpatterns = [
    # REST API
    path('api/', include(router.urls)),

    # Web Views
    path('', views.TransferListView.as_view(), name='transfer-list'),
    path('add/', views.transfer_create, name='transfer-create'),
    path('<int:pk>/', views.TransferDetailView.as_view(), name='transfer-detail'),
    path('<int:pk>/edit/', views.transfer_update, name='transfer-edit'),
    path('<int:pk>/approve/', views.transfer_approve, name='transfer-approve'),
    path('<int:pk>/transit/', views.transfer_start_transit, name='transfer-transit'),
    path('<int:pk>/receive/', views.transfer_receive, name='transfer-receive'),
    path('<int:pk>/reject/', views.transfer_reject, name='transfer-reject'),
    path('<int:pk>/cancel/', views.transfer_cancel, name='transfer-cancel'),
    path('<int:pk>/print/', views.transfer_print, name='transfer-print'),
    path('export/csv/', views.export_transfers_csv, name='transfer-export-csv'),
]
