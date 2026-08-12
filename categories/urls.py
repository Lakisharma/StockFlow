from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryListView, CategoryCreateView, CategoryUpdateView, 
    CategoryDeleteView, CategoryDetailView, category_bulk_delete
)
from .api_views import CategoryViewSet

# REST API Router
router = DefaultRouter()
router.register('api', CategoryViewSet, basename='api-category')

urlpatterns = [
    # Web views
    path('', CategoryListView.as_view(), name='category-list'),
    path('add/', CategoryCreateView.as_view(), name='category-add'),
    path('<int:pk>/edit/', CategoryUpdateView.as_view(), name='category-edit'),
    path('<int:pk>/delete/', CategoryDeleteView.as_view(), name='category-delete'),
    path('<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('bulk-delete/', category_bulk_delete, name='category-bulk-delete'),
    
    # API endpoints
    path('', include(router.urls)),
]
