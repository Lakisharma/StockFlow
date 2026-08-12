from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from products.models import Warehouse
from .models import WarehouseZone, WarehouseBin, WarehouseReorderSetting
from .serializers import WarehouseMasterSerializer, WarehouseZoneSerializer, WarehouseBinSerializer, WarehouseReorderSettingSerializer
from .services import WarehouseService

class WarehouseMasterViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseMasterSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'city', 'manager_name']

class WarehouseZoneViewSet(viewsets.ModelViewSet):
    queryset = WarehouseZone.objects.select_related('warehouse').all()
    serializer_class = WarehouseZoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['zone_code', 'zone_name', 'warehouse__name']

class WarehouseBinViewSet(viewsets.ModelViewSet):
    queryset = WarehouseBin.objects.select_related('zone', 'zone__warehouse').all()
    serializer_class = WarehouseBinSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['bin_code', 'rack', 'shelf', 'zone__zone_code']

class WarehouseReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def comparison(self, request):
        data = WarehouseService.get_warehouse_comparison_data()
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        wh_id = request.query_params.get('warehouse_id')
        data = WarehouseService.get_warehouse_dashboard_metrics(warehouse_id=wh_id, user=request.user)
        return Response(data, status=status.HTTP_200_OK)
