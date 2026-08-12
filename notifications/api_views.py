from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer
from .services import NotificationService

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='header-summary')
    def header_summary(self, request):
        summary = NotificationService.get_user_notifications(request.user)
        serializer = NotificationSerializer(summary['recent'], many=True)
        return Response({
            'unread_count': summary['unread_count'],
            'recent': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='read')
    def mark_read(self, request, pk=None):
        ok = NotificationService.mark_as_read(pk, request.user)
        if ok:
            return Response({'message': 'Notification marked as read.'}, status=status.HTTP_200_OK)
        return Response({'error': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        NotificationService.mark_all_read(request.user)
        return Response({'message': 'All notifications marked as read.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='dispatch-alerts')
    def dispatch_alerts(self, request):
        count = NotificationService.dispatch_stock_alerts()
        return Response({'message': f'Dispatched {count} stock alert notifications.'}, status=status.HTTP_200_OK)

class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)
