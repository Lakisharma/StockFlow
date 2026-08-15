from rest_framework import viewsets, permissions
from django.contrib.auth.models import User
from .models import Role, RolePermission, UserProfile, UserActivityLog
from .serializers import UserSerializer, RoleSerializer, UserActivityLogSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(profile__is_soft_deleted=False).select_related('profile', 'profile__role')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.prefetch_related('permissions').all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class UserActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserActivityLog.objects.select_related('user').all()
    serializer_class = UserActivityLogSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate, login as django_login
import json

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    data = request.data if request.data else {}
    if not data and request.body:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = {}
    username_input = data.get('username', '').strip()
    password = data.get('password', '').strip()

    user_obj = User.objects.filter(username__iexact=username_input).first() or User.objects.filter(email__iexact=username_input).first()
    username = user_obj.username if user_obj else username_input

    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            django_login(request._request, user)
            return Response({
                'success': True,
                'token': 'session_token_' + str(user.id),
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser
            })
        else:
            return Response({'success': False, 'error': 'Account is disabled.'}, status=400)
    return Response({'success': False, 'error': 'Invalid username/email or password.'}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_change_password(request):
    data = request.data if request.data else {}
    if not data and request.body:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = {}
    username = data.get('username', '').strip()
    current_password = data.get('current_password', '').strip()
    new_password = data.get('new_password', '').strip()

    if not username:
        if request.user and request.user.is_authenticated:
            user = request.user
        else:
            return Response({'success': False, 'error': 'Username is required.'}, status=400)
    else:
        user = User.objects.filter(username__iexact=username).first() or User.objects.filter(email__iexact=username).first()

    if not user:
        return Response({'success': False, 'error': 'User not found.'}, status=404)

    if not user.check_password(current_password):
        return Response({'success': False, 'error': 'Current password does not match.'}, status=400)

    if len(new_password) < 6:
        return Response({'success': False, 'error': 'New password must be at least 6 characters.'}, status=400)

    user.set_password(new_password)
    user.save()
    return Response({'success': True, 'message': 'Password changed successfully!'})


