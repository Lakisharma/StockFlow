from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BrandListView, BrandCreateView, BrandUpdateView, 
    BrandDeleteView, BrandDetailView, brand_bulk_delete
)
from .api_views import BrandViewSet

# REST API Router
router = DefaultRouter()
router.register('api', BrandViewSet, basename='api-brand')

urlpatterns = [
    # Web views
    path('', BrandListView.as_view(), name='brand-list'),
    path('add/', BrandCreateView.as_view(), name='brand-add'),
    path('<int:pk>/edit/', BrandUpdateView.as_view(), name='brand-edit'),
    path('<int:pk>/delete/', BrandDeleteView.as_view(), name='brand-delete'),
    path('<int:pk>/', BrandDetailView.as_view(), name='brand-detail'),
    path('bulk-delete/', brand_bulk_delete, name='brand-bulk-delete'),
    
    # API endpoints
    path('', include(router.urls)),
]
