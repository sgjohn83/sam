from rest_framework import serializers

from administration.models import Branch
from documents.models import Document, DocumentType
from .models import Application, ApplicationStatus


class BranchSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "code"]


class ApplicationDetailSerializer(serializers.ModelSerializer):
    status_label = serializers.SerializerMethodField()
    branch_preferences = serializers.SerializerMethodField()
    allocated_branch = BranchSummarySerializer(read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_submit = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "application_number",
            "status",
            "status_label",
            "branch_preferences",
            "submitted_at",
            "allocated_branch",
            "allocated_quota",
            "fee_amount",
            "fee_concession",
            "fee_paid",
            "is_locked",
            "can_edit",
            "can_submit",
            "created_at",
        ]

    def get_status_label(self, obj):
        return obj.get_status_display()

    def get_branch_preferences(self, obj):
        branch_ids = obj.branch_preferences or []
        if not branch_ids:
            return []

        branches = Branch.objects.filter(id__in=branch_ids, is_active=True)
        branch_map = {str(branch.id): branch for branch in branches}
        ordered = [branch_map.get(str(branch_id)) for branch_id in branch_ids]
        ordered = [branch for branch in ordered if branch is not None]
        return BranchSummarySerializer(ordered, many=True).data

    def get_can_edit(self, obj):
        return obj.status == ApplicationStatus.DRAFT and not obj.is_locked

    def get_can_submit(self, obj):
        # Profile is mandatory by model relation; if application exists this is true.
        has_profile = obj.student_id is not None
        uploaded_types = set(
            Document.objects.filter(student=obj.student)
            .values_list("document_type", flat=True)
        )
        required_types = {
            DocumentType.AADHAR,
            DocumentType.MARKSHEET_10,
            DocumentType.MARKSHEET_12,
            DocumentType.RANK_CARD,
        }
        has_all_docs = required_types.issubset(uploaded_types)
        return has_profile and has_all_docs and self.get_can_edit(obj)


class BranchPreferenceSerializer(serializers.Serializer):
    branch_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )

    def validate_branch_ids(self, value):
        if len(value) < 1:
            raise serializers.ValidationError("At least 1 branch must be selected")
        if len(value) > 5:
            raise serializers.ValidationError("Maximum 5 branches allowed")

        unique_ids = list(dict.fromkeys(value))
        if len(unique_ids) != len(value):
            raise serializers.ValidationError("Duplicate branch IDs are not allowed")

        existing = set(
            Branch.objects.filter(id__in=unique_ids, is_active=True)
            .values_list("id", flat=True)
        )
        missing = [str(branch_id) for branch_id in unique_ids if branch_id not in existing]
        if missing:
            raise serializers.ValidationError(
                f"Invalid or inactive branch IDs: {', '.join(missing)}"
            )
        return unique_ids


class ApplicationStatusTimelineSerializer(serializers.Serializer):
    current_status = serializers.CharField()
    timeline = serializers.ListField()

    @staticmethod
    def from_application(application: Application):
        timeline_spec = [
            ("registered", "Registered", application.created_at),
            ("profile_created", "Profile Created", application.student.created_at),
            ("documents_uploaded", "Documents Uploaded", None),
            ("submitted", "Submitted", application.submitted_at),
            ("under_verification", "Under Verification", None),
            ("verified", "Verified", None),
            ("seat_allocated", "Seat Allocated", None),
            ("fee_pending", "Fee Payment", None),
            ("admitted", "Admitted", application.admitted_at),
        ]

        status_order = {
            ApplicationStatus.DRAFT: 1,
            ApplicationStatus.SUBMITTED: 3,
            ApplicationStatus.UNDER_VERIFICATION: 4,
            ApplicationStatus.VERIFIED: 5,
            ApplicationStatus.SEAT_ALLOCATED: 6,
            ApplicationStatus.FEE_PENDING: 7,
            ApplicationStatus.ADMITTED: 8,
            ApplicationStatus.REJECTED: 4,
        }
        current_stage = status_order.get(application.status, 1)

        uploaded_docs = Document.objects.filter(student=application.student)
        has_all_docs = uploaded_docs.count() >= 4
        latest_doc_date = uploaded_docs.order_by("-uploaded_at").values_list("uploaded_at", flat=True).first()

        timeline = []
        for idx, (step, label, date_value) in enumerate(timeline_spec):
            step_index = idx
            completed = step_index <= current_stage

            if step == "documents_uploaded":
                completed = has_all_docs
                date_value = latest_doc_date if has_all_docs else None

            if step == "under_verification" and application.status in {
                ApplicationStatus.UNDER_VERIFICATION,
                ApplicationStatus.VERIFIED,
                ApplicationStatus.SEAT_ALLOCATED,
                ApplicationStatus.FEE_PENDING,
                ApplicationStatus.ADMITTED,
                ApplicationStatus.REJECTED,
            }:
                completed = True
                date_value = application.claimed_at or application.updated_at

            if step == "verified" and application.status in {
                ApplicationStatus.VERIFIED,
                ApplicationStatus.SEAT_ALLOCATED,
                ApplicationStatus.FEE_PENDING,
                ApplicationStatus.ADMITTED,
            }:
                completed = True
                date_value = application.updated_at

            if step == "seat_allocated" and application.allocated_branch_id:
                completed = True
                date_value = application.updated_at

            if step == "fee_pending" and application.status in {
                ApplicationStatus.FEE_PENDING,
                ApplicationStatus.ADMITTED,
            }:
                completed = True
                date_value = application.updated_at

            timeline.append(
                {
                    "step": step,
                    "label": label,
                    "completed": completed,
                    "date": date_value.date().isoformat() if date_value else None,
                }
            )

        return {
            "current_status": application.status,
            "timeline": timeline,
        }


class PaymentProofUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
