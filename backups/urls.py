from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register('records', api_views.BackupRecordViewSet, basename='api-backup-records')
router.register('settings', api_views.BackupSettingsViewSet, basename='api-backup-settings')

urlpatterns = [
    # REST API ViewSets
    path('api/', include(router.urls)),

    # Web Controller Views
    path('', views.BackupDashboardView.as_view(), name='backup-dashboard'),
    path('create/', views.BackupCreateView.as_view(), name='backup-create'),
    path('<int:pk>/', views.BackupDetailView.as_view(), name='backup-detail'),
    path('<int:pk>/download/', views.BackupDownloadView.as_view(), name='backup-download'),
    path('<int:pk>/restore/', views.BackupRestoreView.as_view(), name='backup-restore'),
    path('<int:pk>/delete/', views.BackupDeleteView.as_view(), name='backup-delete'),
    path('settings/save/', views.BackupSettingsView.as_view(), name='backup-settings-save'),
]
