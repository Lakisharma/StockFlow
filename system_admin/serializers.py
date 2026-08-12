from rest_framework import serializers
from .models import DocumentSequence, SecurityPolicy, UserFailedLogin

class DocumentSequenceSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)

    class Meta:
        model = DocumentSequence
        fields = ['id', 'document_type', 'document_type_display', 'prefix', 'next_number', 'padding', 'is_active', 'updated_at']

class SecurityPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityPolicy
        fields = '__all__'

class UserFailedLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFailedLogin
        fields = ['id', 'username', 'ip_address', 'attempt_time', 'is_resolved']
