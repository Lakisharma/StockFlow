from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register('sequences', api_views.DocumentSequenceViewSet, basename='api-doc-seq')
router.register('policies', api_views.SecurityPolicyViewSet, basename='api-security-policy')
router.register('lockout', api_views.UserLockoutViewSet, basename='api-user-lockout')
router.register('health', api_views.SystemHealthViewSet, basename='api-system-health')

urlpatterns = [
    # REST API Router
    path('api/', include(router.urls)),

    # Admin Control Center & Modules
    path('', views.AdminControlCenterView.as_view(), name='admin-control-center'),
    path('security/', views.SecurityDashboardView.as_view(), name='admin-security'),
    path('numbering/', views.DocumentNumberingView.as_view(), name='admin-numbering'),
    path('health/', views.SystemHealthView.as_view(), name='admin-health'),
    path('users/unlock/<int:user_id>/', views.UserLockoutManagementView.as_view(), name='admin-user-unlock'),
]
