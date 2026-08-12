from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .services import ReportAnalyticsService
from .serializers import DashboardMetricsSerializer

class DashboardMetricsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        range_type = request.query_params.get('range_type', 'all')
        c_start = request.query_params.get('start_date')
        c_end = request.query_params.get('end_date')

        s_date, e_date = ReportAnalyticsService.parse_date_range(range_type, c_start, c_end)
        metrics = ReportAnalyticsService.get_dashboard_metrics(s_date, e_date)
        serializer = DashboardMetricsSerializer(metrics)
        return Response(serializer.data, status=status.HTTP_200_OK)

class WarehouseComparisonAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        wh1_id = request.query_params.get('wh1')
        wh2_id = request.query_params.get('wh2')

        if not wh1_id or not wh2_id:
            return Response({'error': 'Please provide both wh1 and wh2 parameters.'}, status=status.HTTP_400_BAD_REQUEST)

        comp = ReportAnalyticsService.get_warehouse_comparison(wh1_id, wh2_id)
        if not comp:
            return Response({'error': 'One or both specified warehouses not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(comp, status=status.HTTP_200_OK)
