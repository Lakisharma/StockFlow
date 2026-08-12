from rest_framework import serializers
from .models import Notification, NotificationPreference

class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'type_display',
            'priority', 'priority_display', 'module', 'related_record_type',
            'related_record_id', 'action_url', 'is_read', 'created_at', 'read_at'
        ]

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = '__all__'
