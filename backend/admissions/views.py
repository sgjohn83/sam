from pathlib import Path
from uuid import uuid4

from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from administration.models import AcademicYear, Branch
from documents.models import Document, DocumentStatus, DocumentType
from documents.services.application_autofill import generate_autofill_data
from notifications.utils import send_email_with_retry, send_push_to_student
from .models import Application, ApplicationStatus, AdmissionChannel
from .serializers import (
    ApplicationDetailSerializer,
    ApplicationStatusTimelineSerializer,
    BranchPreferenceSerializer,
    PaymentProofUploadSerializer,
)


def _get_student_application_for_user(user):
    if not hasattr(user, "student_profile"):
        return None
    app, _ = Application.objects.get_or_create(student=user.student_profile)
    return app


def _get_missing_profile_fields(profile):
    missing = []
    user = profile.user

    if not (user.full_name or "").strip():
        missing.append("full_name")
    if not profile.date_of_birth:
        missing.append("date_of_birth")
    if not profile.gender:
        missing.append("gender")
    if not (profile.mobile_number or "").strip():
        missing.append("mobile_number")

    address = profile.address or {}
    if not isinstance(address, dict):
        missing.append("address")
    else:
        for key in ["street", "city", "state", "pincode"]:
            if not str(address.get(key, "")).strip():
                missing.append(f"address.{key}")

    if not profile.category:
        missing.append("category")
    if not (profile.domicile_state or "").strip():
        missing.append("domicile_state")

    return missing


class StudentApplicationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        application = _get_student_application_for_user(request.user)
        if application is None:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ApplicationDetailSerializer(application).data, status=status.HTTP_200_OK)


class StudentApplicationBranchPreferencesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        application = _get_student_application_for_user(request.user)
        if application is None:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if application.is_locked:
            return Response(
                {"error": "Branch preferences cannot be changed after submission"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BranchPreferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branch_preferences = [
            str(branch_id) for branch_id in serializer.validated_data["branch_ids"]
        ]

        application.branch_preferences = branch_preferences
        application.save(update_fields=["branch_preferences", "updated_at"])
        return Response(ApplicationDetailSerializer(application).data, status=status.HTTP_200_OK)


class StudentApplicationSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        application = _get_student_application_for_user(request.user)
        if application is None:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 1) Application exists and is draft
        if application.status != ApplicationStatus.DRAFT:
            return Response(
                {"error": "Application already submitted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2) Profile complete
        missing_profile_fields = _get_missing_profile_fields(application.student)
        if missing_profile_fields:
            return Response(
                {
                    "error": "Complete your profile before submitting. Missing: "
                    + ", ".join(missing_profile_fields)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3) All required docs uploaded
        student_docs = Document.objects.filter(student=application.student)
        docs_by_type = {doc.document_type: doc for doc in student_docs}
        required_doc_types = [
            DocumentType.AADHAR,
            DocumentType.MARKSHEET_10,
            DocumentType.MARKSHEET_12,
            DocumentType.RANK_CARD,
        ]
        missing_doc_types = [doc_type for doc_type in required_doc_types if doc_type not in docs_by_type]
        if missing_doc_types:
            return Response(
                {
                    "error": "Upload all required documents. Missing: "
                    + ", ".join(missing_doc_types)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4) No rejected/processing docs
        rejected_doc_types = [
            doc_type
            for doc_type, doc in docs_by_type.items()
            if doc.status == DocumentStatus.REJECTED
        ]
        if rejected_doc_types:
            return Response(
                {
                    "error": "Re-upload rejected documents before submitting: "
                    + ", ".join(rejected_doc_types)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        has_processing = any(
            doc.status == DocumentStatus.PROCESSING for doc in docs_by_type.values()
        )
        if has_processing:
            return Response(
                {"error": "Wait for document processing to complete"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 5) At least one branch preference
        if not application.branch_preferences:
            return Response(
                {"error": "Select at least one branch preference"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 6) Admission window open for current academic year
        current_year = AcademicYear.objects.filter(is_current=True).first()
        today = timezone.localdate()
        if (
            current_year is None
            or today < current_year.admission_open_date
            or today > current_year.admission_close_date
        ):
            year_label = current_year.year_label if current_year else "current year"
            return Response(
                {"error": f"Admission window is closed for {year_label}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        branch_ids = [str(branch_id) for branch_id in (application.branch_preferences or [])]
        branch_map = {
            str(branch.id): branch
            for branch in Branch.objects.filter(id__in=branch_ids, is_active=True)
        }
        branch_preference_details = [
            {
                "id": branch_id,
                "name": branch_map[branch_id].name,
                "code": branch_map[branch_id].code,
            }
            for branch_id in branch_ids
            if branch_id in branch_map
        ]

        autofill = generate_autofill_data(application.student_id)

        now = timezone.now()
        application.status = ApplicationStatus.SUBMITTED
        application.submitted_at = now
        application.is_locked = True
        application.locked_at = now
        application.submitted_data = {
            "profile_fields": autofill.get("profile_fields", {}),
            "academic_fields": autofill.get("academic_fields", {}),
            "confidence_summary": autofill.get("confidence_summary", {}),
            "branch_preferences": branch_preference_details,
            "snapshot_at": now.isoformat(),
        }
        application.save(
            update_fields=[
                "status",
                "submitted_at",
                "is_locked",
                "locked_at",
                "submitted_data",
                "updated_at",
            ]
        )

        # Notify student
        subject = f"Application Received - {application.application_number}"
        student_name = (request.user.full_name or "Student").strip()
        submitted_local = timezone.localtime(application.submitted_at or now)
        submitted_display = f"{submitted_local:%B} {submitted_local.day}, {submitted_local:%Y}"
        branch_lines = "\n".join(
            [
                f"{index}. {branch['name']} ({branch['code']})"
                for index, branch in enumerate(branch_preference_details, start=1)
            ]
        ) or "No branch preferences selected"

        body = (
            f"Dear {student_name},\n\n"
            f"Your application ({application.application_number}) has been received successfully.\n\n"
            "Branch Preferences:\n"
            f"{branch_lines}\n\n"
            "Your documents will now be verified by our team. You will receive\n"
            "an update once verification is complete.\n\n"
            f"Submitted: {submitted_display}\n\n"
            "- Admission Portal"
        )
        send_email_with_retry(subject, body, [request.user.email])
        send_push_to_student(
            student_user_id=request.user.id,
            title="Application Submitted",
            body=(
                f"Your application {application.application_number} has been received. "
                "We'll notify you when verification is complete."
            ),
            data={"type": "application_submitted", "application_id": str(application.id)},
        )

        return Response(ApplicationDetailSerializer(application).data, status=status.HTTP_200_OK)


class StudentApplicationStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        application = _get_student_application_for_user(request.user)
        if application is None:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = ApplicationStatusTimelineSerializer.from_application(application)
        return Response(payload, status=status.HTTP_200_OK)


class StudentApplicationPaymentProofUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        application = _get_student_application_for_user(request.user)
        if application is None:
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PaymentProofUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_file = serializer.validated_data["file"]

        extension = Path(uploaded_file.name).suffix.lower() or ".bin"
        relative_path = (
            f"payments/{application.id}/{timezone.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex}{extension}"
        )
        saved_path = default_storage.save(relative_path, uploaded_file)

        application.payment_proof_path = saved_path
        application.fee_paid = False
        application.save(update_fields=["payment_proof_path", "fee_paid", "updated_at"])

        return Response(
            {
                "message": "Payment proof uploaded",
                "payment_proof_path": application.payment_proof_path,
            },
            status=status.HTTP_200_OK,
        )


class ApplicationLockView(APIView):
    """
    POST /api/applications/{id}/lock/
    Lock an application after verification is complete.
    Requires verification staff role.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from accounts.models import User
        from documents.models import Document, DocumentStatus

        if request.user.role not in [User.Role.VERIFICATION_STAFF, User.Role.ADMIN] and not request.user.is_superuser:
            return Response(
                {"error": "Only verification staff can lock applications"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response(
                {"error": "Application not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if application.is_locked:
            return Response(
                {"error": "Application is already locked"},
                status=status.HTTP_400_BAD_REQUEST
            )

        all_docs = Document.objects.filter(student=application.student)
        verified_count = all_docs.filter(status=DocumentStatus.VERIFIED).count()
        total_count = all_docs.count()

        if verified_count < total_count:
            return Response(
                {"error": f"Cannot lock: only {verified_count}/{total_count} documents verified"},
                status=status.HTTP_400_BAD_REQUEST
            )

        application.is_locked = True
        application.locked_at = timezone.now()
        application.locked_by = request.user
        application.save(update_fields=['is_locked', 'locked_at', 'locked_by'])

        from verification.models import AuditLog
        ip = self._get_client_ip(request)
        AuditLog.objects.create(
            entity_type='application',
            entity_id=application.id,
            application=application,
            action='LOCK',
            user=request.user,
            before_json={'is_locked': False},
            after_json={'is_locked': True, 'locked_at': application.locked_at.isoformat()},
            ip_address=ip
        )

        return Response({
            "message": "Application locked successfully",
            "application_id": str(application.id),
            "locked_at": application.locked_at.isoformat()
        }, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class ApplicationUnlockView(APIView):
    """
    POST /api/applications/{id}/unlock/
    Unlock an application. Admin-only, requires reason.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from accounts.models import User

        if not request.user.is_superuser and request.user.role != User.Role.ADMIN:
            return Response(
                {"error": "Only admins can unlock applications"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response(
                {"error": "Application not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        reason = request.data.get('reason')
        if not reason:
            return Response(
                {"error": "Reason is required for unlocking"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not application.is_locked:
            return Response(
                {"error": "Application is not locked"},
                status=status.HTTP_400_BAD_REQUEST
            )

        before_state = {
            'is_locked': True,
            'locked_at': application.locked_at.isoformat() if application.locked_at else None,
            'locked_by': application.locked_by.email if application.locked_by else None
        }

        application.is_locked = False
        application.locked_at = None
        application.locked_by = None
        application.save(update_fields=['is_locked', 'locked_at', 'locked_by'])

        from verification.models import AuditLog
        ip = self._get_client_ip(request)
        AuditLog.objects.create(
            entity_type='application',
            entity_id=application.id,
            application=application,
            action='UNLOCK',
            user=request.user,
            before_json=before_state,
            after_json={'is_locked': False, 'unlock_reason': reason},
            ip_address=ip
        )

        return Response({
            "message": "Application unlocked successfully",
            "application_id": str(application.id)
        }, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class OfficerApplicationListView(APIView):
    """
    GET /officer/applications
    Returns paginated list of verified/locked applications for officers.
    """
    from accounts.permissions import IsAdmissionOfficer
    permission_classes = [permissions.IsAuthenticated, IsAdmissionOfficer]

    def get(self, request):
        from django.db.models import Q

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        offset = (page - 1) * page_size
        limit = offset + page_size

        status_filter = request.query_params.get('status')
        branch_id = request.query_params.get('branch_id')
        quota = request.query_params.get('quota')
        category = request.query_params.get('category')
        domicile_state = request.query_params.get('domicile_state')
        search = request.query_params.get('search', '').strip()
        sort_by = request.query_params.get('sort_by', 'merit_score')
        sort_order = request.query_params.get('sort_order', 'desc')

        queryset = Application.objects.select_related(
            'student', 'student__user', 'allocated_branch'
        ).filter(
            status__in=[
                ApplicationStatus.VERIFIED,
                ApplicationStatus.SEAT_ALLOCATED,
                ApplicationStatus.FEE_PENDING,
                ApplicationStatus.ADMITTED,
                ApplicationStatus.REJECTED,
            ]
        )

        if status_filter:
            status_map = {
                'verified': ApplicationStatus.VERIFIED,
                'locked': ApplicationStatus.VERIFIED,
                'allocated': ApplicationStatus.SEAT_ALLOCATED,
                'fee_pending': ApplicationStatus.FEE_PENDING,
                'admitted': ApplicationStatus.ADMITTED,
                'rejected': ApplicationStatus.REJECTED,
            }
            if status_filter in status_map:
                queryset = queryset.filter(status=status_map[status_filter])

        if branch_id:
            try:
                branch_uuid = uuid4(branch_id)
                queryset = queryset.filter(
                    Q(allocated_branch_id=branch_uuid) |
                    Q(branch_preferences__contains=[str(branch_uuid)])
                )
            except ValueError:
                pass

        if quota:
            queryset = queryset.filter(allocated_quota=quota)

        if category:
            queryset = queryset.filter(student__category=category)

        if domicile_state:
            queryset = queryset.filter(student__domicile_state=domicile_state)

        fee_status_filter = request.query_params.get('fee_status')
        if fee_status_filter:
            if fee_status_filter == 'not_sent':
                queryset = queryset.filter(fee_instruction_sent_at__isnull=True)
            elif fee_status_filter == 'sent':
                queryset = queryset.filter(
                    fee_instruction_sent_at__isnull=False,
                    fee_paid=False
                ).filter(Q(fee_deadline__gte=timezone.now()) | Q(fee_deadline__isnull=True))
            elif fee_status_filter == 'overdue':
                queryset = queryset.filter(
                    fee_instruction_sent_at__isnull=False,
                    fee_paid=False,
                    fee_deadline__lt=timezone.now()
                )
            elif fee_status_filter == 'paid':
                queryset = queryset.filter(fee_paid=True)

        if search:
            queryset = queryset.filter(
                Q(application_number__icontains=search) |
                Q(student__user__full_name__icontains=search)
            )

        sort_fields = {
            'merit_score': 'fee_amount',
            'submitted_at': 'submitted_at',
            'application_number': 'application_number',
        }

        if sort_by in sort_fields:
            order_field = sort_fields[sort_by]
            queryset = queryset.order_by(order_field if sort_order == 'asc' else f'-{order_field}')
        else:
            queryset = queryset.order_by('-fee_amount')

        total_count = queryset.count()
        paginated_qs = queryset[offset:limit]

        results = []
        for app in paginated_qs:
            student = app.student
            user = student.user if student else None
            
            # Compute fee status
            fee_status = 'not_sent'
            if app.fee_paid:
                fee_status = 'paid'
            elif app.fee_instruction_sent_at:
                if app.fee_deadline and app.fee_deadline < timezone.now():
                    fee_status = 'overdue'
                else:
                    fee_status = 'sent'
            
            results.append({
                'application_id': str(app.id),
                'application_number': app.application_number,
                'student_name': user.full_name if user else None,
                'status': app.status,
                'branch_preferences': app.branch_preferences or [],
                'category': getattr(student, 'category', None),
                'domicile_state': getattr(student, 'domicile_state', None),
                'allocated_branch': app.allocated_branch.name if app.allocated_branch else None,
                'allocated_branch_id': str(app.allocated_branch_id) if app.allocated_branch_id else None,
                'allocated_quota': app.allocated_quota,
                'merit_score': float(app.fee_amount) if app.fee_amount else None,
                'submitted_at': app.submitted_at.isoformat() if app.submitted_at else None,
                'locked_at': app.locked_at.isoformat() if app.locked_at else None,
                'is_locked': app.is_locked,
                # Fee-related fields
                'fee_status': fee_status,
                'fee_amount': float(app.fee_amount) if app.fee_amount else None,
                'fee_deadline': app.fee_deadline.isoformat() if app.fee_deadline else None,
                'fee_instruction_sent_at': app.fee_instruction_sent_at.isoformat() if app.fee_instruction_sent_at else None,
                'fee_paid': app.fee_paid,
            })

        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': results
        })


class OfficerApplicationDetailView(APIView):
    """
    GET /officer/applications/{id}
    Returns full read-only view of a single application.
    """
    from accounts.permissions import IsAdmissionOfficer
    permission_classes = [permissions.IsAuthenticated, IsAdmissionOfficer]

    def get(self, request, pk):
        from django.db.models import Avg
        from documents.models import Document, DocumentStatus
        from verification.models import AuditLog

        try:
            application = Application.objects.select_related(
                'student', 'student__user', 'allocated_branch'
            ).prefetch_related(
                'student__documents',
                'student__documents__ocr_results'
            ).get(pk=pk)
        except Application.DoesNotExist:
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        student = application.student
        user = student.user if student else None
        documents = student.documents.all() if student else []

        # Build documents metadata
        documents_data = []
        for doc in documents:
            ocr_result = doc.get_latest_ocr_result()
            documents_data.append({
                'document_id': str(doc.id),
                'document_type': doc.document_type,
                'document_label': doc.get_document_type_display(),
                'status': doc.status,
                'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                'upload_version': doc.upload_version,
                'rejection_reason': doc.rejection_reason,
                'rejection_category': doc.rejection_category,
                'is_rejected': doc.rejection_reason is not None and doc.rejection_reason != '',
                'ocr_confidence': float(ocr_result.overall_confidence) if ocr_result else None,
                'extracted_fields': ocr_result.extracted_fields if ocr_result else None,
                'confidence_scores': ocr_result.confidence_scores if ocr_result else None,
            })

        # Verification status per document
        verification_status = {}
        for doc in documents:
            ocr_result = doc.get_latest_ocr_result()
            if ocr_result:
                from verification.services import compute_field_states
                field_states = compute_field_states(ocr_result.id)
                verified_count = sum(1 for s in field_states.values() if s in ['approved', 'edited'])
                total_fields = len(field_states)
                verification_status[doc.document_type] = {
                    'verified_fields': verified_count,
                    'total_fields': total_fields,
                    'is_complete': verified_count == total_fields and total_fields > 0
                }

        # Audit trail summary (last 10 entries)
        audit_logs = AuditLog.objects.filter(
            application=application
        ).select_related('user').order_by('-timestamp')[:10]

        audit_trail = []
        for log in audit_logs:
            audit_trail.append({
                'id': str(log.id),
                'action': log.action,
                'user_email': log.user.email if log.user else None,
                'before_json': log.before_json,
                'after_json': log.after_json,
                'timestamp': log.timestamp.isoformat(),
            })

        # Merit score breakdown (using fee_amount as proxy)
        merit_breakdown = {
            'total_score': float(application.fee_amount) if application.fee_amount else 0,
            'base_score': float(application.fee_amount * 0.7) if application.fee_amount else 0,
            'additional_score': float(application.fee_amount * 0.3) if application.fee_amount else 0,
            'quota_bonus': 0,
        }

        # Student profile data
        student_profile = None
        if student:
            student_profile = {
                'student_id': str(student.id),
                'full_name': user.full_name if user else None,
                'email': user.email if user else None,
                'mobile_number': student.mobile_number,
                'date_of_birth': student.date_of_birth.isoformat() if student.date_of_birth else None,
                'gender': student.gender,
                'category': student.category,
                'domicile_state': student.domicile_state,
                'address': student.address,
                'parent_name': student.parent_name,
                'parent_phone': student.parent_phone,
            }

        # Lock information
        lock_info = {
            'is_locked': application.is_locked,
            'locked_at': application.locked_at.isoformat() if application.locked_at else None,
            'locked_by': application.locked_by.email if application.locked_by else None,
            'immutable_fields': [
                'student_name', 'date_of_birth', 'category', 'domicile_state',
                'document_data', 'extracted_fields', 'verification_status'
            ] if application.is_locked else [],
        }

        # Build response
        response_data = {
            'application_id': str(application.id),
            'application_number': application.application_number,
            'status': application.status,
            'submitted_at': application.submitted_at.isoformat() if application.submitted_at else None,
            'is_locked': application.is_locked,
            'lock_info': lock_info,
            'student_profile': student_profile,
            'branch_preferences': application.branch_preferences or [],
            'allocated_branch': application.allocated_branch.name if application.allocated_branch else None,
            'allocated_branch_id': str(application.allocated_branch_id) if application.allocated_branch_id else None,
            'allocated_quota': application.allocated_quota,
            'fee_amount': float(application.fee_amount) if application.fee_amount else None,
            'fee_concession': float(application.fee_concession) if application.fee_concession else None,
            'fee_paid': application.fee_paid,
            'merit_score': float(application.fee_amount) if application.fee_amount else None,
            'merit_breakdown': merit_breakdown,
            'documents': documents_data,
            'verification_status': verification_status,
            'audit_trail': audit_trail,
        }

        return Response(response_data)


class OfficerDashboardStatsView(APIView):
    """
    GET /officer/dashboard/stats
    Returns aggregated counts for the dashboard header.
    Cached in Redis with 60s TTL.
    """
    from accounts.permissions import IsAdmissionOfficer
    from django.core.cache import cache
    permission_classes = [permissions.IsAuthenticated, IsAdmissionOfficer]

    CACHE_KEY = 'officer_dashboard_stats'
    CACHE_TTL = 60  # seconds

    def get(self, request):
        cached_data = cache.get(self.CACHE_KEY)
        if cached_data is not None:
            return Response(cached_data)

        # Build stats
        stats = self._build_stats()
        
        # Cache the result
        cache.set(self.CACHE_KEY, stats, self.CACHE_TTL)
        
        return Response(stats)

    def _build_stats(self):
        from django.db.models import Count, Q
        from administration.models import Branch

        # Applications by status
        status_counts = Application.objects.aggregate(
            total=Count('id'),
            verified=Count('id', filter=Q(status=ApplicationStatus.VERIFIED)),
            locked=Count('id', filter=Q(is_locked=True)),
            allocated=Count('id', filter=Q(status=ApplicationStatus.SEAT_ALLOCATED)),
            fee_pending=Count('id', filter=Q(status=ApplicationStatus.FEE_PENDING)),
            admitted=Count('id', filter=Q(status=ApplicationStatus.ADMITTED)),
            rejected=Count('id', filter=Q(status=ApplicationStatus.REJECTED)),
        )

        # Applications per branch (allocated)
        branch_stats = []
        branches = Branch.objects.annotate(
            application_count=Count('application', filter=Q(
                application__status__in=[
                    ApplicationStatus.VERIFIED,
                    ApplicationStatus.SEAT_ALLOCATED,
                    ApplicationStatus.FEE_PENDING,
                    ApplicationStatus.ADMITTED
                ]
            ))
        ).values('id', 'name', 'total_seats', 'application_count')

        for branch in branches:
            branch_stats.append({
                'branch_id': str(branch['id']),
                'branch_name': branch['name'],
                'total_seats': branch['total_seats'] or 0,
                'applications': branch['application_count'],
                'available_seats': max(0, (branch['total_seats'] or 0) - branch['application_count']),
            })

        # Applications per quota type
        quota_counts = Application.objects.filter(
            status__in=[
                ApplicationStatus.VERIFIED,
                ApplicationStatus.SEAT_ALLOCATED,
                ApplicationStatus.FEE_PENDING,
                ApplicationStatus.ADMITTED,
            ]
        ).values('allocated_quota').annotate(count=Count('id'))

        quota_stats = {}
        for item in quota_counts:
            quota_type = item['allocated_quota'] or 'unassigned'
            quota_stats[quota_type] = item['count']

        # Category distribution
        category_counts = Application.objects.filter(
            status__in=[
                ApplicationStatus.VERIFIED,
                ApplicationStatus.SEAT_ALLOCATED,
                ApplicationStatus.FEE_PENDING,
                ApplicationStatus.ADMITTED,
            ]
        ).values('student__category').annotate(count=Count('id'))

        category_stats = {}
        for item in category_counts:
            cat = item['student__category'] or 'unassigned'
            category_stats[cat] = item['count']

        return {
            'by_status': {
                'total': status_counts['total'],
                'verified': status_counts['verified'],
                'locked': status_counts['locked'],
                'allocated': status_counts['allocated'],
                'fee_pending': status_counts['fee_pending'],
                'admitted': status_counts['admitted'],
                'rejected': status_counts['rejected'],
            },
            'by_branch': branch_stats,
            'by_quota': quota_stats,
            'by_category': category_stats,
            'cached_at': timezone.now().isoformat(),
        }


class WalkinRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.db import transaction
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError

        data = request.data
        required_fields = [
            'full_name', 'email', 'phone', 'date_of_birth', 'gender',
            'category', 'domicile_state', 'branch_preferences'
        ]

        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = data.get('email', '').strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"error": "Invalid email format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        branch_prefs = data.get('branch_preferences', [])
        if not branch_prefs or not isinstance(branch_prefs, list):
            return Response(
                {"error": "At least one branch preference is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                user = User.objects.filter(email=email).first()
                student = None

                if user and hasattr(user, 'student_profile'):
                    student = user.student_profile
                    application = Application.objects.filter(student=student).first()
                    if application:
                        return Response({
                            "student_id": str(student.id),
                            "application_id": str(application.id),
                            "application_number": application.application_number,
                            "message": "Existing student and application returned",
                        }, status=status.HTTP_200_OK)
                else:
                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        full_name=data.get('full_name', ''),
                        password=User.objects.make_random_password(),
                    )
                    user.role = User.Role.STUDENT
                    user.save()

                    from students.models import StudentProfile
                    student = StudentProfile.objects.create(
                        user=user,
                        date_of_birth=data.get('date_of_birth'),
                        gender=data.get('gender'),
                        mobile_number=data.get('phone'),
                        category=data.get('category'),
                        domicile_state=data.get('domicile_state'),
                        address=data.get('address', {}),
                    )

                application = Application.objects.create(
                    student=student,
                    branch_preferences=[str(bp) for bp in branch_prefs],
                    status=ApplicationStatus.DRAFT,
                    admission_channel=AdmissionChannel.WALKIN,
                )

                return Response({
                    "student_id": str(student.id),
                    "application_id": str(application.id),
                    "application_number": application.application_number,
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"Registration failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WalkinDocumentScanView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request, application_id):
        from accounts.permissions import IsAdmissionOfficer
        from documents.models import Document, DocumentType, DocumentStatus, OCRPriority
        from django.core.files.storage import default_storage
        from django.conf import settings
        import os
        import uuid

        if not request.user.role in [User.Role.ADMIN, User.Role.OFFICER]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = Application.objects.get(pk=application_id)
        except Application.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

        document_type = request.data.get('document_type')
        if not document_type:
            return Response({"error": "document_type is required"}, status=status.HTTP_400_BAD_REQUEST)

        if document_type not in DocumentType.values:
            return Response(
                {"error": f"Invalid document_type. Must be one of: {', '.join(DocumentType.values)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({"error": "file is required"}, status=status.HTTP_400_BAD_REQUEST)

        allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
        if uploaded_file.content_type not in allowed_types:
            return Response(
                {"error": "Invalid file type. Allowed: JPG, PNG, PDF"},
                status=status.HTTP_400_BAD_REQUEST
            )

        max_size = 5 * 1024 * 1024
        if uploaded_file.size > max_size:
            return Response({"error": "File too large. Max 5MB allowed"}, status=status.HTTP_400_BAD_REQUEST)

        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        unique_name = f"{uuid.uuid4()}{file_ext}"
        file_path = f"walkin/{application.id}/{unique_name}"

        saved_path = default_storage.save(file_path, uploaded_file)

        document = Document.objects.create(
            student=application.student,
            document_type=document_type,
            file_path=saved_path,
            file_name=uploaded_file.name,
            file_size_bytes=uploaded_file.size,
            mime_type=uploaded_file.content_type,
            status=DocumentStatus.PROCESSING,
            uploaded_by=request.user,
            ocr_priority=OCRPriority.HIGH,
        )

        from documents.services.ocr_service import process_document
        from django.db import transaction
        
        ocr_job_id = None
        try:
            with transaction.atomic():
                result = process_document(document.id)
                ocr_job_id = str(result.id) if result else None
        except Exception as ocr_error:
            logger.warning(f"OCR processing failed for document {document.id}: {ocr_error}")
            document.status = DocumentStatus.PROCESSING

        return Response({
            "document_id": str(document.id),
            "ocr_job_id": ocr_job_id,
            "status": document.status,
        }, status=status.HTTP_201_CREATED)


class WalkinDocumentOCRStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, application_id, document_id):
        from documents.models import Document, OCRResult

        if not request.user.role in [User.Role.ADMIN, User.Role.OFFICER]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = Application.objects.get(pk=application_id)
        except Application.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            document = Document.objects.get(pk=document_id, student=application.student)
        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

        ocr_result = OCRResult.objects.filter(document=document).order_by('-created_at').first()

        if not ocr_result:
            return Response({
                "status": "processing",
                "fields": None,
                "confidence_scores": None,
            }, status=status.HTTP_200_OK)

        return Response({
            "status": document.status,
            "fields": ocr_result.extracted_fields,
            "confidence_scores": ocr_result.confidence_scores,
            "overall_confidence": ocr_result.overall_confidence,
        }, status=status.HTTP_200_OK)


class WalkinInlineVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, application_id):
        from documents.models import Document, DocumentStatus
        from verification.models import FieldVerification, AuditLog
        from django.db import transaction

        if not request.user.role in [User.Role.ADMIN, User.Role.OFFICER]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = Application.objects.get(pk=application_id)
        except Application.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

        if application.admission_channel != AdmissionChannel.WALKIN:
            return Response(
                {"error": "Inline verification only for walk-in applications"},
                status=status.HTTP_400_BAD_REQUEST
            )

        documents_data = request.data.get('documents', [])
        if not documents_data:
            return Response(
                {"error": "documents array is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        audit_logs = []

        with transaction.atomic():
            for doc_data in documents_data:
                document_id = doc_data.get('document_id')
                corrected_fields = doc_data.get('fields', {})

                try:
                    document = Document.objects.select_for_update().get(
                        pk=document_id,
                        student=application.student
                    )
                except Document.DoesNotExist:
                    return Response(
                        {"error": f"Document {document_id} not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                ocr_result = document.ocr_results.order_by('-created_at').first()
                if not ocr_result:
                    return Response(
                        {"error": f"No OCR result for document {document_id}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                current_fields = ocr_result.extracted_fields or {}
                for field_name, corrected_value in corrected_fields.items():
                    old_value = current_fields.get(field_name)
                    if old_value != corrected_value:
                        current_fields[field_name] = corrected_value

                        FieldVerification.objects.create(
                            document=document,
                            field_name=field_name,
                            original_value=str(old_value) if old_value else None,
                            corrected_value=str(corrected_value),
                            verified_by=request.user,
                            status='approved',
                        )

                        audit_logs.append(AuditLog(
                            entity_type='document',
                            entity_id=document.id,
                            action='field_corrected',
                            actor=request.user,
                            before_json={'field': field_name, 'value': old_value},
                            after_json={'field': field_name, 'value': corrected_value},
                        ))

                ocr_result.extracted_fields = current_fields
                ocr_result.save(update_fields=['extracted_fields'])

                document.status = DocumentStatus.VERIFIED
                document.save(update_fields=['status'])

                audit_logs.append(AuditLog(
                    entity_type='document',
                    entity_id=document.id,
                    action='document_verified',
                    actor=request.user,
                    before_json={'status': str(document.status)},
                    after_json={'status': DocumentStatus.VERIFIED},
                ))

            application.status = ApplicationStatus.VERIFIED
            application.is_locked = True
            application.locked_at = timezone.now()
            application.locked_by = request.user
            application.save(update_fields=['status', 'is_locked', 'locked_at', 'locked_by'])

            audit_logs.append(AuditLog(
                entity_type='application',
                entity_id=application.id,
                action='walkin_verified_and_locked',
                actor=request.user,
                before_json={'status': 'draft', 'is_locked': False},
                after_json={'status': ApplicationStatus.VERIFIED, 'is_locked': True},
            ))

            if audit_logs:
                AuditLog.objects.bulk_create(audit_logs)

        self._calculate_merit_score(application)

        return Response({
            "application_id": str(application.id),
            "application_number": application.application_number,
            "status": application.status,
            "is_locked": application.is_locked,
            "message": "Walk-in verification complete, application locked",
        }, status=status.HTTP_200_OK)

    def _calculate_merit_score(self, application):
        from documents.models import Document, DocumentType
        from django.db.models import Max

        marks_10 = Document.objects.filter(
            student=application.student,
            document_type=DocumentType.MARKSHEET_10,
            status=DocumentStatus.VERIFIED,
        ).annotate(
            latest_ocr=Max('ocr_results__created_at')
        ).first()

        marks_12 = Document.objects.filter(
            student=application.student,
            document_type=DocumentType.MARKSHEET_12,
            status=DocumentStatus.VERIFIED,
        ).annotate(
            latest_ocr=Max('ocr_results__created_at')
        ).first()

        score_10 = 0.0
        score_12 = 0.0

        if marks_10:
            ocr = marks_10.ocr_results.order_by('-created_at').first()
            if ocr and ocr.extracted_fields:
                pct = ocr.extracted_fields.get('percentage') or ocr.extracted_fields.get('cgpa', 0)
                score_10 = float(pct) * 10

        if marks_12:
            ocr = marks_12.ocr_results.order_by('-created_at').first()
            if ocr and ocr.extracted_fields:
                pct = ocr.extracted_fields.get('percentage') or ocr.extracted_fields.get('cgpa', 0)
                score_12 = float(pct) * 10

        rank_card = Document.objects.filter(
            student=application.student,
            document_type=DocumentType.RANK_CARD,
            status=DocumentStatus.VERIFIED,
        ).first()

        rank_score = 0.0
        if rank_card:
            ocr = rank_card.ocr_results.order_by('-created_at').first()
            if ocr and ocr.extracted_fields:
                rank = ocr.extracted_fields.get('overall_rank')
                if rank:
                    rank_score = max(0, 1000 - int(rank))

        total_score = score_10 + score_12 + rank_score
        application.fee_amount = total_score
        application.save(update_fields=['fee_amount'])


class WalkinAllocateAndNotifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, application_id):
        from seats.engine import allocate_seat, SeatUnavailableError
        from administration.models import Branch, FeeStructure
        import uuid
        from datetime import timedelta

        if not request.user.role in [User.Role.ADMIN, User.Role.OFFICER]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = Application.objects.get(pk=application_id)
        except Application.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

        if application.admission_channel != AdmissionChannel.WALKIN:
            return Response(
                {"error": "This endpoint is only for walk-in applications"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not application.is_locked:
            return Response(
                {"error": "Application must be locked before allocation"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if application.status != ApplicationStatus.VERIFIED:
            return Response(
                {"error": f"Application must be verified, current: {application.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if application.allocated_branch_id:
            return Response(
                {"error": "Seat already allocated to this application"},
                status=status.HTTP_400_BAD_REQUEST
            )

        branch_id = request.data.get('branch_id')
        quota = request.data.get('quota')
        fee_deadline_days = request.data.get('fee_deadline_days', 7)

        if not branch_id or not quota:
            return Response(
                {"error": "branch_id and quota are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            branch = Branch.objects.get(pk=branch_id, is_active=True)
        except Branch.DoesNotExist:
            return Response({"error": "Invalid branch_id"}, status=status.HTTP_400_BAD_REQUEST)

        fee_structure = FeeStructure.objects.filter(branch=branch, academic_year=application.academic_year).first()
        fee_amount = fee_structure.tuition_fee if fee_structure else 0

        try:
            allocate_seat(application.id, branch_id, quota, actor=request.user)
        except SeatUnavailableError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        application.refresh_from_db()

        payment_ref = f"PAY-{application.application_number}-{uuid.uuid4().hex[:6].upper()}"
        fee_deadline = timezone.now() + timedelta(days=int(fee_deadline_days))

        application.fee_amount = fee_amount
        application.payment_reference_id = payment_ref
        application.fee_deadline = fee_deadline
        application.status = ApplicationStatus.FEE_PENDING
        application.save(update_fields=[
            'fee_amount', 'payment_reference_id', 'fee_deadline', 'status', 'updated_at'
        ])

        self._send_fee_notification(application, branch, fee_amount, payment_ref, fee_deadline)

        return Response({
            "application_id": str(application.id),
            "application_number": application.application_number,
            "status": application.status,
            "allocated_branch": branch.name,
            "allocated_quota": quota,
            "fee_amount": float(fee_amount),
            "payment_reference_id": payment_ref,
            "fee_deadline": fee_deadline.isoformat(),
            "fee_instruction_sent_at": application.fee_instruction_sent_at.isoformat() if application.fee_instruction_sent_at else None,
            "message": "Seat allocated and fee notification sent",
        }, status=status.HTTP_200_OK)

    def _send_fee_notification(self, application, branch, fee_amount, payment_ref, fee_deadline):
        from admissions.services.fee import notify_fee_payment

        try:
            notify_fee_payment(application)
            application.fee_instruction_sent_at = timezone.now()
            application.save(update_fields=['fee_instruction_sent_at'])
        except Exception as e:
            logger.warning(f"Failed to send fee notification: {e}")


def calculate_fee(application_id):
    """
    Calculate fee for an application.
    Returns { line_items: [...], total, concession, net_payable }.
    """
    from administration.models import FeeStructure, AcademicYear

    application = Application.objects.get(pk=application_id)
    if not application.allocated_branch:
        return None

    current_year = AcademicYear.objects.filter(is_current=True).first()
    if not current_year:
        return None

    fee_structures = FeeStructure.objects.filter(
        branch=application.allocated_branch,
        academic_year=current_year,
        is_active=True,
    )

    line_items = []
    total = 0

    for fs in fee_structures:
        amount = float(fs.tuition_fee or 0) + float(fs.hostel_fee or 0) + float(fs.lab_fee or 0) + float(fs.other_charges or 0)
        line_items.append({
            "fee_type": fs.fee_type,
            "tuition_fee": float(fs.tuition_fee or 0),
            "hostel_fee": float(fs.hostel_fee or 0),
            "lab_fee": float(fs.lab_fee or 0),
            "other_charges": float(fs.other_charges or 0),
            "total": amount,
        })
        total += amount

    concession = float(application.fee_concession or 0)
    net_payable = max(total - concession, 0)

    return {
        "line_items": line_items,
        "total": total,
        "concession": concession,
        "net_payable": net_payable,
    }


class CalculateFeeView(APIView):
    """
    GET /officer/applications/{id}/calculate-fee/
    Returns fee breakdown for an allocated application.
    """
    from accounts.permissions import IsAdmissionOfficer
    permission_classes = [permissions.IsAuthenticated, IsAdmissionOfficer]

    def get(self, request, pk):
        fee_data = calculate_fee(pk)
        if not fee_data:
            return Response(
                {"error": "Fee calculation not possible - branch not allocated or fee structure missing"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(fee_data)


class SendFeeInstructionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        import uuid
        from datetime import timedelta
        from verification.models import AuditLog
        from administration.models import FeeStructure, AcademicYear

        if not request.user.role in [User.Role.ADMIN, User.Role.OFFICER]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

        if application.status != ApplicationStatus.SEAT_ALLOCATED:
            return Response(
                {"error": f"Application must be in seat_allocated status, current: {application.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not application.allocated_branch:
            return Response(
                {"error": "No branch allocated to this application"},
                status=status.HTTP_400_BAD_REQUEST
            )

        fee_calculated = calculate_fee(application.id)
        if not fee_calculated:
            return Response(
                {"error": "Could not calculate fee - no fee structure found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        fee_deadline_days = request.data.get('fee_deadline_days', 7)
        payment_ref = f"PAY-{application.application_number}-{uuid.uuid4().hex[:6].upper()}"
        fee_deadline = timezone.now() + timedelta(days=int(fee_deadline_days))

        application.fee_amount = fee_calculated['net_payable']
        application.fee_deadline = fee_deadline
        application.payment_reference_id = payment_ref
        application.status = ApplicationStatus.FEE_PENDING
        application.save(update_fields=[
            'fee_amount', 'fee_deadline', 'payment_reference_id', 'status', 'updated_at'
        ])

        self._send_fee_email(application, fee_calculated, payment_ref, fee_deadline)

        AuditLog.objects.create(
            entity_type='application',
            entity_id=application.id,
            application=application,
            action='fee_instructions_sent',
            user=request.user,
            before_json={'fee_amount': None},
            after_json={'fee_amount': fee_calculated['net_payable'], 'payment_ref': payment_ref},
        )

        return Response({
            "application_id": str(application.id),
            "application_number": application.application_number,
            "status": application.status,
            "fee_amount": fee_calculated['net_payable'],
            "payment_reference_id": payment_ref,
            "fee_deadline": fee_deadline.isoformat(),
            "message": "Fee instructions sent successfully",
        }, status=status.HTTP_200_OK)

    def _send_fee_email(self, application, fee_data, payment_ref, fee_deadline):
        student = application.student
        user = student.user

        subject = f"Fee Payment Details - {application.application_number}"
        context = {
            "student_name": user.full_name,
            "application_number": application.application_number,
            "branch_name": application.allocated_branch.name,
            "quota": application.allocated_quota,
            "line_items": fee_data['line_items'],
            "total": fee_data['total'],
            "concession": fee_data['concession'],
            "net_payable": fee_data['net_payable'],
            "payment_reference": payment_ref,
            "fee_deadline": fee_deadline.strftime("%d-%m-%Y"),
            "bank_details": {
                "account_name": "College Name",
                "account_number": "XXXXXXXXXX",
                "ifsc_code": "XXXXXXXXXX",
                "bank_name": "Bank Name",
            },
            "contact_info": "admissions@college.edu | +91-XXXXXXXXXX",
        }

        try:
            send_email_with_retry(
                to_email=user.email,
                subject=subject,
                template_name="fee_payment_instructions.html",
                context=context,
            )
            application.fee_instruction_sent_at = timezone.now()
            application.save(update_fields=['fee_instruction_sent_at'])
        except Exception as e:
            logger.warning(f"Failed to send fee email: {e}")


class ResendFeeInstructionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from verification.models import AuditLog

        if not request.user.role in [User.Role.ADMIN, User.Role.OFFICER]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

        if not application.allocated_branch:
            return Response(
                {"error": "No branch allocated to this application"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not application.payment_reference_id:
            return Response(
                {"error": "Fee instructions not yet sent. Use send-fee-instructions first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        fee_calculated = calculate_fee(application.id)
        if not fee_calculated:
            return Response(
                {"error": "Could not calculate fee"},
                status=status.HTTP_400_BAD_REQUEST
            )

        self._send_fee_email(application, fee_calculated, application.payment_reference_id, application.fee_deadline)

        AuditLog.objects.create(
            entity_type='application',
            entity_id=application.id,
            application=application,
            action='fee_instructions_resent',
            user=request.user,
        )

        return Response({
            "message": "Fee instructions resent successfully",
            "fee_instruction_sent_at": application.fee_instruction_sent_at.isoformat(),
        }, status=status.HTTP_200_OK)

    def _send_fee_email(self, application, fee_data, payment_ref, fee_deadline):
        from admissions.services.fee import notify_fee_payment
        
        try:
            notify_fee_payment(application)
            application.fee_instruction_sent_at = timezone.now()
            application.save(update_fields=['fee_instruction_sent_at'])
        except Exception as e:
            logger.warning(f"Failed to resend fee email: {e}")


class ConfirmPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from verification.models import AuditLog
        from seats.cache import invalidate_seat_cache

        if not request.user.role in [User.Role.ADMIN, User.Role.OFFICER]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

        if application.status != ApplicationStatus.SEAT_ALLOCATED:
            return Response(
                {"error": f"Application must be in seat_allocated status, current: {application.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not application.fee_amount or application.fee_amount <= 0:
            return Response(
                {"error": "Fee amount not set for this application"},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_past_deadline = False
        if application.fee_deadline and application.fee_deadline < timezone.now():
            is_past_deadline = True
            override = request.data.get('override_deadline', False)
            if not override:
                return Response(
                    {
                        "warning": "Payment deadline has passed",
                        "deadline": application.fee_deadline.isoformat(),
                        "override_required": True,
                        "message": "Set override_deadline=true in request body to confirm anyway"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        payment_proof_path = request.data.get('payment_proof_path')

        application.fee_paid = True
        application.fee_paid_at = timezone.now()
        application.status = ApplicationStatus.ADMITTED
        application.admitted_at = timezone.now()
        if payment_proof_path:
            application.payment_proof_path = payment_proof_path
        application.save(update_fields=[
            'fee_paid', 'fee_paid_at', 'status', 'admitted_at', 'payment_proof_path', 'updated_at'
        ])

        if application.allocated_branch_id and application.allocated_quota:
            invalidate_seat_cache(
                branch_id=application.allocated_branch_id,
                quota=application.allocated_quota
            )

        AuditLog.objects.create(
            entity_type='application',
            entity_id=application.id,
            application=application,
            action='payment_confirmed_admitted',
            user=request.user,
            before_json={'status': ApplicationStatus.SEAT_ALLOCATED, 'fee_paid': False},
            after_json={'status': ApplicationStatus.ADMITTED, 'fee_paid': True},
        )

        self._send_admission_confirmation_email(application)

        return Response({
            "application_id": str(application.id),
            "application_number": application.application_number,
            "status": application.status,
            "fee_paid": application.fee_paid,
            "fee_paid_at": application.fee_paid_at.isoformat(),
            "admitted_at": application.admitted_at.isoformat(),
            "message": "Payment confirmed, admission completed",
        }, status=status.HTTP_200_OK)

    def _send_admission_confirmation_email(self, application):
        from admissions.services.fee import notify_admission_confirmation
        
        try:
            notify_admission_confirmation(application)
        except Exception as e:
            logger.warning(f"Failed to send admission confirmation email: {e}")
