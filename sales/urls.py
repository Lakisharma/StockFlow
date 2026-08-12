from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register('customers', api_views.CustomerViewSet, basename='api-customer')
router.register('orders', api_views.SalesOrderViewSet, basename='api-so')
router.register('dispatches', api_views.DispatchViewSet, basename='api-dispatch')
router.register('invoices', api_views.SalesInvoiceViewSet, basename='api-invoice')

urlpatterns = [
    # REST API Router
    path('api/', include(router.urls)),

    # Customer Management Web Views
    path('customers/', views.CustomerListView.as_view(), name='customer-list'),

    # Sales Order Web Views
    path('orders/', views.SalesOrderListView.as_view(), name='so-list'),
    path('orders/create/', views.SalesOrderCreateView.as_view(), name='so-create'),
    path('orders/<int:pk>/', views.SalesOrderDetailView.as_view(), name='so-detail'),
    path('orders/<int:pk>/print/', views.SalesOrderPrintView.as_view(), name='so-print'),

    # Picking Interface
    path('picking/create/', views.PickingCreateView.as_view(), name='picking-create'),

    # Dispatch & Stock-Out Web Views
    path('dispatches/', views.DispatchListView.as_view(), name='dispatch-list'),
    path('dispatches/<int:pk>/confirm/', views.DispatchConfirmView.as_view(), name='dispatch-confirm'),

    # Sales Invoice Web Views
    path('invoices/', views.SalesInvoiceListView.as_view(), name='invoice-list'),
    path('invoices/<int:pk>/', views.SalesInvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoices/<int:pk>/print/', views.SalesInvoicePrintView.as_view(), name='invoice-print'),
]
