from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register('master', api_views.WarehouseMasterViewSet, basename='api-wh-master')
router.register('zones', api_views.WarehouseZoneViewSet, basename='api-wh-zone')
router.register('bins', api_views.WarehouseBinViewSet, basename='api-wh-bin')
router.register('reports', api_views.WarehouseReportViewSet, basename='api-wh-report')

urlpatterns = [
    # REST API Router
    path('api/', include(router.urls)),

    # Dashboard & Master Directory
    path('dashboard/', views.MultiWarehouseDashboardView.as_view(), name='warehouse-dashboard'),
    path('', views.WarehouseListView.as_view(), name='warehouse-list'),
    path('<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse-detail'),

    # Zones & Bins Management
    path('zones/', views.WarehouseZoneBinListView.as_view(), name='warehouse-zones'),

    # Multi-Warehouse Comparison Report
    path('comparison/', views.WarehouseComparisonView.as_view(), name='warehouse-comparison'),
]
