from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupplierListView, SupplierCreateView, SupplierUpdateView, 
    SupplierDeleteView, SupplierDetailView, supplier_bulk_action
)
from .api_views import SupplierViewSet, SupplierHistoryViewSet

# REST API Router
router = DefaultRouter()
router.register('api/suppliers', SupplierViewSet, basename='api-supplier')
router.register('api/history', SupplierHistoryViewSet, basename='api-history')

urlpatterns = [
    # Web views
    path('', SupplierListView.as_view(), name='supplier-list'),
    path('add/', SupplierCreateView.as_view(), name='supplier-add'),
    path('<int:pk>/edit/', SupplierUpdateView.as_view(), name='supplier-edit'),
    path('<int:pk>/delete/', SupplierDeleteView.as_view(), name='supplier-delete'),
    path('<int:pk>/', SupplierDetailView.as_view(), name='supplier-detail'),
    path('bulk-action/', supplier_bulk_action, name='supplier-bulk-action'),
    
    # API endpoints
    path('', include(router.urls)),
]
