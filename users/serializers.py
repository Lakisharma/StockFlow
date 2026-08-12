from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Role, RolePermission, UserProfile, UserActivityLog

class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = ['id', 'module', 'can_view', 'can_create', 'can_edit', 'can_delete', 'can_export', 'can_approve', 'can_print']

class RoleSerializer(serializers.ModelSerializer):
    permissions = RolePermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'is_system_role', 'permissions', 'created_at']

class UserProfileSerializer(serializers.ModelSerializer):
    role_name = serializers.ReadOnlyField(source='role.name')

    class Meta:
        model = UserProfile
        fields = ['phone', 'profile_image', 'role', 'role_name', 'warehouse_access_type', 'assigned_warehouses', 'status', 'is_soft_deleted']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'last_login', 'profile']

class UserActivityLogSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = UserActivityLog
        fields = ['id', 'user', 'username', 'action', 'module', 'reference', 'ip_address', 'timestamp']
