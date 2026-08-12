from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UnitListView, UnitCreateView, UnitUpdateView, 
    UnitDeleteView, UnitDetailView, unit_bulk_delete
)
from .api_views import UnitViewSet

# REST API Router
router = DefaultRouter()
router.register('api', UnitViewSet, basename='api-unit')

urlpatterns = [
    # Web views
    path('', UnitListView.as_view(), name='unit-list'),
    path('add/', UnitCreateView.as_view(), name='unit-add'),
    path('<int:pk>/edit/', UnitUpdateView.as_view(), name='unit-edit'),
    path('<int:pk>/delete/', UnitDeleteView.as_view(), name='unit-delete'),
    path('<int:pk>/', UnitDetailView.as_view(), name='unit-detail'),
    path('bulk-delete/', unit_bulk_delete, name='unit-bulk-delete'),
    
    # API endpoints
    path('', include(router.urls)),
]
