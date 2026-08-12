from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

# REST API Router
router = DefaultRouter()
router.register('orders', api_views.PurchaseOrderViewSet, basename='api-order')
router.register('grn', api_views.GoodsReceiptNoteViewSet, basename='api-grn')
router.register('payments', api_views.PurchasePaymentViewSet, basename='api-payment')
router.register('returns', api_views.PurchaseReturnViewSet, basename='api-return')

urlpatterns = [
    # REST API Router
    path('api/', include(router.urls)),

    # Purchase Orders Web Views
    path('orders/', views.PurchaseOrderListView.as_view(), name='po-list'),
    path('orders/create/', views.PurchaseOrderCreateView.as_view(), name='po-create'),
    path('orders/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='po-detail'),
    path('orders/<int:pk>/print/', views.PurchaseOrderPrintView.as_view(), name='po-print'),

    # Goods Receipt Note (GRN) Web Views
    path('grn/', views.GRNListView.as_view(), name='grn-list'),
    path('grn/create/', views.GRNCreateView.as_view(), name='grn-create'),
    path('grn/<int:pk>/confirm/', views.GRNConfirmView.as_view(), name='grn-confirm'),
    path('grn/<int:pk>/print/', views.GRNPrintView.as_view(), name='grn-print'),

    # Invoice & Detail Aliases for Reports
    path('detail/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='purchase-detail'),
    path('list/', views.PurchaseOrderListView.as_view(), name='purchase-list'),
    path('add/', views.PurchaseOrderCreateView.as_view(), name='purchase-add'),
]
