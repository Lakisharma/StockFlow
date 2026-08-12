from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register('items', api_views.NotificationViewSet, basename='api-notifications')
router.register('preferences', api_views.NotificationPreferenceViewSet, basename='api-notification-preferences')

urlpatterns = [
    # REST API ViewSets
    path('api/', include(router.urls)),

    # Web Controller Views
    path('', views.NotificationCenterView.as_view(), name='notification-center'),
    path('read/<int:pk>/', views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('mark-all-read/', views.NotificationMarkReadView.as_view(), name='notification-mark-all-read'),
    path('delete/<int:pk>/', views.NotificationDeleteView.as_view(), name='notification-delete'),
    path('preferences/', views.NotificationPreferencesView.as_view(), name='notification-preferences'),
]
