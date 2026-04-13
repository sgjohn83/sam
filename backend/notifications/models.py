from django.db import models
from django.conf import settings
import uuid


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=50)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=15, default='pending')
    retry_count = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.notification_type} for {self.recipient.email}"


class NotificationLog(models.Model):
    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        PUSH = 'push', 'Push Notification'
        SMS = 'sms', 'SMS'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_logs')
    channel = models.CharField(max_length=10, choices=Channel.choices)
    template_name = models.CharField(max_length=100, null=True, blank=True)
    subject = models.CharField(max_length=255, null=True, blank=True)
    body_preview = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error = models.TextField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    related_object_id = models.UUIDField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.channel} - {self.status} - {self.user.email}"


class DevicePlatform(models.TextChoices):
    IOS = 'ios', 'iOS'
    ANDROID = 'android', 'Android'


class DeviceToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_tokens',
    )
    expo_push_token = models.CharField(max_length=200, unique=True)
    platform = models.CharField(max_length=10, choices=DevicePlatform.choices)
    device_name = models.CharField(max_length=200, null=True, blank=True)
    app_version = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def clean(self):
        import re
        pattern = r'^ExponentPushToken\[[A-Za-z0-9_-]+\]$'
        if self.expo_push_token and not re.match(pattern, self.expo_push_token):
            from django.core.exceptions import ValidationError
            raise ValidationError({
                'expo_push_token': 'Invalid Expo push token format. Must match ^ExponentPushToken\\[[A-Za-z0-9_-]+\\]'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.platform} - {self.expo_push_token[:20]}..."
