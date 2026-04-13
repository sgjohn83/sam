from rest_framework import serializers
from admissions.models import Application
from documents.models import Document, OCRResult, RejectionCategory
from students.models import StudentProfile
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from .services import compute_cross_verification, compute_verification_progress, compute_field_states

class VerificationQueueSerializer(serializers.ModelSerializer):
    application_id = serializers.UUIDField(source='id')
    student_name = serializers.CharField(source='student.user.full_name')
    student_email = serializers.EmailField(source='student.user.email')
    time_since_submission = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    documents_summary = serializers.SerializerMethodField()
    overall_confidence = serializers.SerializerMethodField()
    confidence_badge = serializers.SerializerMethodField()
    is_claimed = serializers.SerializerMethodField()
    rejected_documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = [
            'application_id', 'application_number', 'student_name', 'student_email',
            'submitted_at', 'time_since_submission', 'documents_count',
            'documents_summary', 'overall_confidence', 'confidence_badge',
            'is_claimed', 'claimed_by', 'claimed_at', 'rejected_documents_count'
        ]
        
    def get_time_since_submission(self, obj):
        if not obj.submitted_at:
            return "N/A"
        now = timezone.now()
        diff = now - obj.submitted_at
        if diff.days > 0:
            return f"{diff.days} days ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours} hours ago"
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes} minutes ago"
        return "Just now"

    def get_documents_count(self, obj):
        # Using prefetch_related if available, otherwise query
        return obj.student.documents.count()

    def _get_conf_data(self, obj):
        if not hasattr(obj, '_conf_data'):
            from .services import compute_application_confidence
            obj._conf_data = compute_application_confidence(obj.id)
        return obj._conf_data

    def get_documents_summary(self, obj):
        conf_data = self._get_conf_data(obj)
        return conf_data['documents'] if conf_data else []

    def get_overall_confidence(self, obj):
        conf_data = self._get_conf_data(obj)
        return conf_data['overall_confidence'] if conf_data else 0.0

    def get_confidence_badge(self, obj):
        conf_data = self._get_conf_data(obj)
        if not conf_data:
            return {"level": "low", "color": "red", "label": "Unknown"}
        
        badge = conf_data['badge'].copy()
        labels = {
            "high": "Clear",
            "medium": "Needs Review",
            "low": "High Risk"
        }
        badge['label'] = labels.get(badge['level'], "N/A")
        return badge

    def get_is_claimed(self, obj):
        if not obj.claimed_by:
            return False
        thirty_min_ago = timezone.now() - timedelta(minutes=30)
        return obj.claimed_at >= thirty_min_ago

    def get_rejected_documents_count(self, obj):
        return obj.student.documents.filter(
            rejection_reason__isnull=False
        ).exclude(rejection_reason='').count()

class SplitScreenOCRResultSerializer(serializers.ModelSerializer):
    field_states = serializers.SerializerMethodField()

    class Meta:
        model = OCRResult
        fields = [
            'id', 'ocr_version', 'extracted_fields', 'confidence_scores',
            'overall_confidence', 'field_states'
        ]

    def get_field_states(self, obj):
        return compute_field_states(obj.id)


class SplitScreenDocumentSerializer(serializers.ModelSerializer):
    document_label = serializers.CharField(source='get_document_type_display')
    file_url = serializers.SerializerMethodField()
    ocr_result = SplitScreenOCRResultSerializer(source='get_latest_ocr_result', allow_null=True)
    is_rejected = serializers.SerializerMethodField()
    rejection_reason = serializers.CharField(source='rejection_reason', allow_null=True)
    rejection_category = serializers.CharField(source='rejection_category', allow_null=True)
    reupload_requested_at = serializers.DateTimeField(source='reupload_requested_at', allow_null=True)

    class Meta:
        model = Document
        fields = [
            'id', 'document_type', 'document_label', 'status', 'file_url',
            'mime_type', 'upload_version', 'uploaded_at', 'ocr_result',
            'is_rejected', 'rejection_reason', 'rejection_category', 'reupload_requested_at'
        ]

    def get_is_rejected(self, obj):
        return obj.rejection_reason is not None and obj.rejection_reason != ''

    def get_file_url(self, obj):
        # TODO: generate actual file URL
        return f"/api/documents/{obj.id}/file/"


class SplitScreenStudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name')
    email = serializers.EmailField(source='user.email')
    mobile_number = serializers.CharField()

    class Meta:
        model = StudentProfile
        fields = ['id', 'full_name', 'email', 'mobile_number']


class SplitScreenApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            'id', 'application_number', 'status', 'is_locked',
            'claimed_by', 'claimed_at', 'claim_expires_at', 'submitted_at'
        ]

    claim_expires_at = serializers.SerializerMethodField()

    def get_claim_expires_at(self, obj):
        if obj.claimed_at:
            return obj.claimed_at + timedelta(minutes=30)
        return None


class SplitScreenSerializer(serializers.Serializer):
    # This is not a ModelSerializer; we'll populate data manually
    application = SplitScreenApplicationSerializer(source='*')
    student = SplitScreenStudentSerializer(source='student')
    documents = SplitScreenDocumentSerializer(source='student.documents', many=True)
    cross_verification = serializers.SerializerMethodField()
    verification_progress = serializers.SerializerMethodField()

    def get_cross_verification(self, obj):
        return compute_cross_verification(obj.id)

    def get_verification_progress(self, obj):
        return compute_verification_progress(obj.id)


class FieldEditRequestSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    field_name = serializers.CharField(max_length=100)
    new_value = serializers.CharField(allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class FieldEditResponseSerializer(serializers.Serializer):
    field_name = serializers.CharField()
    old_value = serializers.CharField(allow_null=True)
    new_value = serializers.CharField(allow_null=True)
    state = serializers.CharField()
    verified_by = serializers.SerializerMethodField()
    verified_at = serializers.DateTimeField()

    def get_verified_by(self, obj):
        if obj.verified_by:
            return obj.verified_by.email
        return None


class FieldApproveRequestSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    field_name = serializers.CharField(max_length=100)


class FieldApproveResponseSerializer(serializers.Serializer):
    field_name = serializers.CharField()
    old_value = serializers.CharField(allow_null=True)
    new_value = serializers.CharField(allow_null=True)
    state = serializers.CharField()
    verified_by = serializers.SerializerMethodField()
    verified_at = serializers.DateTimeField()

    def get_verified_by(self, obj):
        if obj.verified_by:
            return obj.verified_by.email
        return None


class BulkApproveRequestSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()


class DocumentVerifyResponseSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    document_type = serializers.CharField()
    status = serializers.CharField()
    verified_fields = serializers.ListField(child=serializers.CharField())
    pending_fields = serializers.ListField(child=serializers.CharField())


class DocumentRejectionSerializer(serializers.Serializer):
    rejection_category = serializers.ChoiceField(choices=RejectionCategory.choices)
    rejection_reason = serializers.CharField(max_length=1000, required=True)
    notify_student = serializers.BooleanField(default=True)

    def validate_rejection_reason(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Rejection reason must be at least 10 characters long.")
        return value


class OCRResultHistorySerializer(serializers.Serializer):
    ocr_version = serializers.IntegerField()
    overall_confidence = serializers.FloatField()
    field_count = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()

    def get_field_count(self, obj):
        return len(obj.extracted_fields) if obj.extracted_fields else 0


class ReuploadHistoryEventSerializer(serializers.Serializer):
    event_type = serializers.CharField()
    timestamp = serializers.DateTimeField()
    details = serializers.DictField()
    actor = serializers.SerializerMethodField()
    version = serializers.IntegerField(allow_null=True)

    def get_actor(self, obj):
        return obj.get('actor')


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True, allow_null=True)
    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    user_role = serializers.CharField(source='user.role', read_only=True, allow_null=True)
    application_number = serializers.SerializerMethodField()

    class Meta:
        from .models import AuditLog
        model = AuditLog
        fields = [
            'id', 'user', 'user_name', 'user_email', 'user_role',
            'application', 'application_number',
            'entity_type', 'entity_id', 'action', 'field_name',
            'old_value', 'new_value', 'before_json', 'after_json',
            'ip_address', 'user_agent', 'timestamp',
        ]
        read_only_fields = fields

    def get_application_number(self, obj):
        return obj.application.application_number if obj.application else None
