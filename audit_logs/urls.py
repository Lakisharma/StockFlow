from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register('logs', api_views.SystemAuditLogViewSet, basename='api-audit-logs')

urlpatterns = [
    # REST API Endpoint
    path('api/', include(router.urls)),

    # Web Controller Views
    path('', views.AuditLogListView.as_view(), name='audit-log-list'),
    path('timeline/', views.AuditLogTimelineView.as_view(), name='audit-log-timeline'),
    path('<int:pk>/', views.AuditLogDetailView.as_view(), name='audit-log-detail'),
    path('export/csv/', views.AuditLogExportView.as_view(), name='audit-log-export'),
]
