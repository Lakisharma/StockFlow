"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from app.views import login, forgot_password, dashboard
from core.views import GlobalSearchView, HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login, name='login'),
    path('forgot-password/', forgot_password, name='forgot-password'),
    path('dashboard/', dashboard, name='dashboard'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('api/search/', GlobalSearchView.as_view(), name='global-search-api'),
    path('categories/', include('categories.urls')),
    path('units/', include('units.urls')),
    path('brands/', include('brands.urls')),
    path('products/', include('products.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('purchases/', include('purchases.urls')),
    path('inventory/', include('inventory.urls')),
    path('transfers/', include('transfers.urls')),
    path('ocr/', include('ocr_scanner.urls')),
    path('reports/', include('reports.urls')),
    path('users/', include('users.urls')),
    path('settings/', include('settings_app.urls')),
    path('backups/', include('backups.urls')),
    path('audit-logs/', include('audit_logs.urls')),
    path('notifications/', include('notifications.urls')),
    path('barcodes/', include('barcodes.urls')),
    path('batches/', include('batches.urls')),
    path('sales/', include('sales.urls')),
    path('payments/', include('payments.urls')),
    path('accounting/', include('accounting.urls')),
    path('employees/', include('employees.urls')),
    path('warehouses/', include('warehouses.urls')),
    path('analytics/', include('analytics.urls')),
    path('admin-center/', include('system_admin.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.custom_404_view'
handler500 = 'core.views.custom_500_view'
handler403 = 'core.views.custom_403_view'
