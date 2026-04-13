from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
import json
import uuid

class DocumentType(models.TextChoices):
    AADHAR = 'aadhar', 'Aadhar Card'
    MARKSHEET_10 = 'marksheet_10', '10th Marksheet'
    MARKSHEET_12 = 'marksheet_12', '12th Marksheet'
    RANK_CARD = 'rank_card', 'Entrance Rank Card'

class DocumentStatus(models.TextChoices):
    PROCESSING = 'processing', 'Processing'
    EXTRACTED = 'extracted', 'Extracted'
    VERIFIED = 'verified', 'Verified'
    REJECTED = 'rejected', 'Rejected'


class RejectionCategory(models.TextChoices):
    BLURRY = 'blurry', 'Blurry Image'
    WRONG_DOCUMENT = 'wrong_document', 'Wrong Document'
    INCOMPLETE = 'incomplete', 'Incomplete Document'
    EXPIRED = 'expired', 'Expired Document'
    MISMATCH = 'mismatch', 'Data Mismatch'
    UNREADABLE = 'unreadable', 'Unreadable'
    OTHER = 'other', 'Other'


class OCRPriority(models.TextChoices):
    LOW = 'low', 'Low'
    NORMAL = 'normal', 'Normal'
    HIGH = 'high', 'High'

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    file_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=255)
    file_size_bytes = models.IntegerField(validators=[MinValueValidator(0)])
    mime_type = models.CharField(max_length=50)
    upload_version = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.PROCESSING)
    rejection_reason = models.TextField(null=True, blank=True)
    rejection_category = models.CharField(max_length=50, choices=RejectionCategory.choices, null=True, blank=True)
    rejected_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='rejected_documents')
    rejected_at = models.DateTimeField(null=True, blank=True)
    reupload_requested_at = models.DateTimeField(null=True, blank=True)
    reupload_count = models.IntegerField(default=0)
    ocr_priority = models.CharField(
        max_length=10,
        choices=OCRPriority.choices,
        default=OCRPriority.NORMAL,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'document_type'], name='unique_doc_per_type_per_student'),
            models.CheckConstraint(check=models.Q(file_size_bytes__lte=5242880), name='file_size_limit_check'),
        ]

    def __str__(self):
        return f"{self.document_type} - {self.student.user.full_name}"

    def get_latest_ocr_result(self):
        """Returns OCRResult with highest ocr_version for this document."""
        return self.ocr_results.order_by("-ocr_version").first()

    def get_ocr_history(self):
        """Returns all OCR results ordered by version descending."""
        return self.ocr_results.order_by("-ocr_version")

class OCRResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='ocr_results')
    raw_text = models.TextField()
    extracted_fields = models.JSONField()
    confidence_scores = models.JSONField()
    overall_confidence = models.FloatField()
    processing_duration_ms = models.IntegerField()
    ocr_version = models.IntegerField()
    llm_model_used = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['document', 'ocr_version'], name='unique_ocr_version_per_doc'),
        ]

    def __str__(self):
        return f"OCR for {self.document.document_type} (v{self.ocr_version})"

    def clean(self):
        super().clean()
        try:
            json.dumps(self.extracted_fields)
        except (TypeError, ValueError) as exc:
            raise ValidationError({"extracted_fields": "Must be valid JSON data."}) from exc

    def save(self, *args, **kwargs):
        # Always align OCR result version with current document upload version.
        self.ocr_version = self.document.upload_version
        self.full_clean()
        super().save(*args, **kwargs)
