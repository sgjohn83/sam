import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import PermissionDenied


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_actions'
    )
    application = models.ForeignKey(
        'admissions.Application',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    entity_type = models.CharField(max_length=50, db_index=True)   # "application", "document", "ocr_result"
    entity_id = models.UUIDField(db_index=True)
    action = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100, null=True, blank=True)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    before_json = models.JSONField(null=True, blank=True)
    after_json = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id', '-timestamp']),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise PermissionDenied("Audit logs are append-only and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Audit logs cannot be deleted.")

    def __str__(self):
        return f"{self.user} - {self.action} - {self.entity_type}:{self.entity_id}"


class FieldVerificationState(models.TextChoices):
    PENDING  = 'pending', 'Pending Review'
    APPROVED = 'approved', 'Approved'
    EDITED   = 'edited', 'Edited by Staff'
    FLAGGED  = 'flagged', 'Flagged for Re-upload'


class FieldVerification(models.Model):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document         = models.ForeignKey('documents.Document', on_delete=models.CASCADE, related_name='field_verifications')
    ocr_result       = models.ForeignKey('documents.OCRResult', on_delete=models.CASCADE)
    field_name       = models.CharField(max_length=100)
    original_value   = models.TextField(null=True, blank=True)   # from OCR
    current_value    = models.TextField(null=True, blank=True)   # after edits
    confidence       = models.FloatField()
    state            = models.CharField(max_length=20, choices=FieldVerificationState.choices, default=FieldVerificationState.PENDING)
    verified_by      = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    verified_at      = models.DateTimeField(null=True, blank=True)
    notes            = models.TextField(null=True, blank=True)
    is_superseded    = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['document', 'field_name', 'ocr_result'], name='unique_field_per_ocr_result'),
        ]
        indexes = [
            models.Index(fields=['document', 'state']),
        ]

    def __str__(self):
        return f"{self.document.document_type}.{self.field_name} - {self.state}"
