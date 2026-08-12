from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # REST API Endpoint
    path('api/all/', api_views.SystemSettingsAPIView.as_view(), name='api-settings-all'),

    # Web Settings View
    path('', views.SettingsMainView.as_view(), name='settings-index'),
]
