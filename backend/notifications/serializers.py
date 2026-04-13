import re
from rest_framework import serializers
from .models import DeviceToken

EXPO_TOKEN_RE = re.compile(r'^ExponentPushToken\[[A-Za-z0-9_-]+\]$')


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['expo_push_token', 'platform', 'device_name', 'app_version']

    def validate_expo_push_token(self, value):
        if not EXPO_TOKEN_RE.match(value):
            raise serializers.ValidationError("Invalid Expo push token format.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        token, _ = DeviceToken.objects.update_or_create(
            expo_push_token=validated_data['expo_push_token'],
            defaults={
                'user': user,
                'platform': validated_data['platform'],
                'device_name': validated_data.get('device_name'),
                'app_version': validated_data.get('app_version'),
                'is_active': True,
            },
        )
        return token
