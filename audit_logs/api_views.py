from rest_framework import viewsets, permissions
from .models import SystemAuditLog
from .serializers import SystemAuditLogSerializer

class SystemAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SystemAuditLog.objects.all()
    serializer_class = SystemAuditLogSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        module = self.request.query_params.get('module')
        action = self.request.query_params.get('action')

        if user_id:
            qs = qs.filter(user_id=user_id)
        if module:
            qs = qs.filter(module=module)
        if action:
            qs = qs.filter(action=action)
        return qs
