from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register('records', api_views.ProductBatchViewSet, basename='api-batches')
router.register('serials', api_views.ProductSerialNumberViewSet, basename='api-serials')

urlpatterns = [
    # REST API ViewSets
    path('api/', include(router.urls)),

    # Web Controller Views
    path('', views.BatchListView.as_view(), name='batch-list'),
    path('expiry/expiring-soon/', views.ExpiringSoonReportView.as_view(), name='expiring-soon-report'),
    path('expiry/expired/', views.ExpiredStockReportView.as_view(), name='expired-stock-report'),
    path('serials/', views.SerialNumberListView.as_view(), name='serial-list'),
    path('serials/<int:pk>/', views.SerialNumberDetailView.as_view(), name='serial-detail'),
]
