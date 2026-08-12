from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BackupRecord, BackupSettings
from .serializers import BackupRecordSerializer, BackupSettingsSerializer
from .services import BackupEngineService

class BackupRecordViewSet(viewsets.ModelViewSet):
    queryset = BackupRecord.objects.all()
    serializer_class = BackupRecordSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['post'], url_path='create-backup')
    def trigger_backup(self, request):
        custom_name = request.data.get('backup_name')
        record = BackupEngineService.create_backup(user=request.user, backup_type='manual', custom_name=custom_name)
        return Response(BackupRecordSerializer(record).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='restore')
    def trigger_restore(self, request, pk=None):
        record = self.get_object()
        BackupEngineService.restore_backup(record, user=request.user)
        return Response({'message': f"Backup {record.backup_id} restored successfully."}, status=status.HTTP_200_OK)

class BackupSettingsViewSet(viewsets.ModelViewSet):
    queryset = BackupSettings.objects.all()
    serializer_class = BackupSettingsSerializer
    permission_classes = [permissions.IsAdminUser]
