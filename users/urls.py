from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # REST API ViewSets
    path('login/', api_views.api_login, name='api-login'),
    path('api/list/', api_views.UserViewSet.as_view({'get': 'list'}), name='api-users-list'),
    path('api/roles/', api_views.RoleViewSet.as_view({'get': 'list'}), name='api-roles-list'),
    path('api/logs/', api_views.UserActivityLogViewSet.as_view({'get': 'list'}), name='api-activity-logs'),

    # User Web Views
    path('', views.UserListView.as_view(), name='user-list'),
    path('add/', views.UserCreateView.as_view(), name='user-add'),
    path('<int:pk>/edit/', views.UserUpdateView.as_view(), name='user-edit'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/deactivate/', views.UserDeactivateView.as_view(), name='user-deactivate'),
    path('<int:pk>/delete/', views.UserSoftDeleteView.as_view(), name='user-delete'),
    path('<int:pk>/reset-password/', views.UserResetPasswordView.as_view(), name='user-reset-password'),
    path('profile/', views.SelfProfileView.as_view(), name='self-profile'),

    # Role & Permission Matrix Web Views
    path('roles/', views.RoleListView.as_view(), name='role-list'),
    path('roles/add/', views.RoleCreateView.as_view(), name='role-add'),
    path('roles/<int:pk>/edit/', views.RoleUpdateView.as_view(), name='role-edit'),
    path('roles/<int:pk>/delete/', views.RoleDeleteView.as_view(), name='role-delete'),

    # Audit Logs
    path('logs/', views.UserActivityLogView.as_view(), name='user-activity-logs'),
]
