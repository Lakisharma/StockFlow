from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import DocumentSequence, SecurityPolicy, UserFailedLogin
from .serializers import DocumentSequenceSerializer, SecurityPolicySerializer, UserFailedLoginSerializer
from .services import SystemAdminService, SystemHealthService

class DocumentSequenceViewSet(viewsets.ModelViewSet):
    queryset = DocumentSequence.objects.all()
    serializer_class = DocumentSequenceSerializer
    permission_classes = [permissions.IsAdminUser]

class SecurityPolicyViewSet(viewsets.ModelViewSet):
    queryset = SecurityPolicy.objects.all()
    serializer_class = SecurityPolicySerializer
    permission_classes = [permissions.IsAdminUser]

class UserLockoutViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'], url_path='locked')
    def get_locked_users(self, request):
        from users.models import UserProfile
        locked_profiles = UserProfile.objects.select_related('user').filter(status='inactive')
        users_data = [{'user_id': p.user.id, 'username': p.user.username, 'email': p.user.email} for p in locked_profiles]
        return Response(users_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='unlock')
    def unlock_user(self, request):
        user_id = request.data.get('user_id')
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        SystemAdminService.unlock_user_account(user)
        return Response({'success': True, 'message': f"Account '{user.username}' unlocked successfully."}, status=status.HTTP_200_OK)

class SystemHealthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'])
    def check(self, request):
        results = SystemHealthService.run_health_check()
        return Response(results, status=status.HTTP_200_OK)
