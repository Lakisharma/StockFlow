from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductListView, ProductCreateView, ProductUpdateView, 
    ProductDeleteView, ProductDetailView, product_bulk_action,
    WarehouseListView, WarehouseCreateView, WarehouseUpdateView, 
    WarehouseDeleteView, WarehouseDetailView, warehouse_bulk_action
)
from .api_views import (
    ProductViewSet, WarehouseViewSet, ProductHistoryViewSet,
    WarehouseStockViewSet, WarehouseHistoryViewSet
)

# REST API Router
router = DefaultRouter()
router.register('api/warehouses', WarehouseViewSet, basename='api-warehouse')
router.register('api/products', ProductViewSet, basename='api-product')
router.register('api/history', ProductHistoryViewSet, basename='api-history')
router.register('api/stocks', WarehouseStockViewSet, basename='api-stock')
router.register('api/warehouse-history', WarehouseHistoryViewSet, basename='api-warehouse-history')

urlpatterns = [
    # Product web views
    path('', ProductListView.as_view(), name='product-list'),
    path('add/', ProductCreateView.as_view(), name='product-add'),
    path('<int:pk>/edit/', ProductUpdateView.as_view(), name='product-edit'),
    path('<int:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('low-stock/', ProductListView.as_view(), name='low-stock-list'),
    path('out-of-stock/', ProductListView.as_view(), name='out-of-stock-list'),
    path('bulk-action/', product_bulk_action, name='product-bulk-action'),
    
    # Warehouse web views
    path('warehouses/', WarehouseListView.as_view(), name='warehouse-list'),
    path('warehouses/add/', WarehouseCreateView.as_view(), name='warehouse-add'),
    path('warehouses/<int:pk>/edit/', WarehouseUpdateView.as_view(), name='warehouse-edit'),
    path('warehouses/<int:pk>/delete/', WarehouseDeleteView.as_view(), name='warehouse-delete'),
    path('warehouses/<int:pk>/', WarehouseDetailView.as_view(), name='warehouse-detail'),
    path('warehouses/bulk-action/', warehouse_bulk_action, name='warehouse-bulk-action'),
    
    # API endpoints
    path('', include(router.urls)),
]
