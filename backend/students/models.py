from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Gender(models.TextChoices):
    MALE = 'male', _('Male')
    FEMALE = 'female', _('Female')
    OTHER = 'other', _('Other')

class StudentCategory(models.TextChoices):
    GENERAL = 'general', _('General')
    OBC = 'obc', _('OBC')
    SC = 'sc', _('SC')
    ST = 'st', _('ST')

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, null=True, blank=True)
    mobile_number = models.CharField(max_length=15)
    address = models.JSONField(null=True, blank=True) # {street, city, state, pincode}
    category = models.CharField(max_length=20, choices=StudentCategory.choices, null=True, blank=True)
    domicile_state = models.CharField(max_length=100, null=True, blank=True)
    agent = models.ForeignKey('agents.AgentProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.full_name}'s Profile"


class PushToken(models.Model):
    class Platform(models.TextChoices):
        IOS = "ios", _("iOS")
        ANDROID = "android", _("Android")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_tokens",
    )
    token = models.TextField()
    platform = models.CharField(max_length=10, choices=Platform.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "token"], name="uniq_push_token_per_user")
        ]

    def __str__(self):
        return f"{self.user.email} [{self.platform}]"
