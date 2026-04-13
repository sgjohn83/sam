from rest_framework import serializers
from .models import User, OTPVerification

class UserSerializer(serializers.ModelSerializer):
    agent_data = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role', 'agent_data']
        read_only_fields = ['id', 'role', 'agent_data']

    def get_agent_data(self, obj):
        if obj.role == 'agent' and hasattr(obj, 'agent_profile'):
            return {
                'agency_name': obj.agent_profile.agency_name,
                'is_verified': obj.agent_profile.is_verified,
            }
        return None

class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)

class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()
