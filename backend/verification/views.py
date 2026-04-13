from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.utils import timezone
from datetime import timedelta
from admissions.models import Application, ApplicationStatus
from accounts.models import User
from .serializers import (
    VerificationQueueSerializer, SplitScreenSerializer,
    FieldEditRequestSerializer, FieldEditResponseSerializer,
    FieldApproveRequestSerializer, FieldApproveResponseSerializer,
    BulkApproveRequestSerializer, DocumentVerifyResponseSerializer,
    DocumentRejectionSerializer, ReuploadHistoryEventSerializer
)
from .guards import check_application_lock

class IsVerificationStaff(permissions.BasePermission):
    """
    Allows access only to verification staff, admins, or superusers.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return (
            request.user.role == User.Role.VERIFICATION_STAFF or 
            request.user.role == User.Role.ADMIN or
            request.user.is_superuser
        )

class VerificationQueueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for the Verification Queue.
    Returns applications that are submitted or under verification and are not currently claimed.
    """
    serializer_class = VerificationQueueSerializer
    permission_classes = [IsVerificationStaff]
    
    def get_queryset(self):
        thirty_min_ago = timezone.now() - timedelta(minutes=30)
        
        queryset = Application.objects.filter(
            status__in=[ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_VERIFICATION]
        ).select_related('student', 'student__user').prefetch_related(
            'student__documents', 
            'student__documents__ocr_results'
        )
        
        # Annotation for sorting/filtering by confidence
        # Simplified to average of all OCR results associated with the student's documents
        queryset = queryset.annotate(
            avg_confidence=Avg('student__documents__ocr_results__overall_confidence')
        )
        
        # --- Filtering ---
        
        # Search: name, application number, email
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(student__user__full_name__icontains=search) |
                Q(application_number__icontains=search) |
                Q(student__user__email__icontains=search)
            )
            
        # Status Filter
        status_param = self.request.query_params.get('status')
        if status_param in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_VERIFICATION]:
            queryset = queryset.filter(status=status_param)
            
        # Confidence Level Filter
        confidence_level = self.request.query_params.get('confidence')
        if confidence_level == 'low':
            queryset = queryset.filter(avg_confidence__lt=0.70)
        elif confidence_level == 'medium':
            queryset = queryset.filter(avg_confidence__gte=0.70, avg_confidence__lt=0.90)
        elif confidence_level == 'high':
            queryset = queryset.filter(avg_confidence__gte=0.90)
            
        # --- Sorting ---
        sort_by = self.request.query_params.get('sort', 'confidence')
        if sort_by == 'confidence':
            queryset = queryset.order_by('avg_confidence')
        elif sort_by == 'confidence_desc':
            queryset = queryset.order_by('-avg_confidence')
        elif sort_by == 'submitted_at':
            queryset = queryset.order_by('submitted_at')
        elif sort_by == '-submitted_at':
            queryset = queryset.order_by('-submitted_at')
        else:
            # Default fallback (redundant but safe)
            queryset = queryset.order_by('avg_confidence')
            
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Use standard DRF pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def _get_client_info(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        return ip, user_agent

    @action(detail=True, methods=['post'])
    def claim(self, request, pk=None):
        application = self.get_object()
        now = timezone.now()
        thirty_min_ago = now - timedelta(minutes=30)

        # 1. Check status
        if application.status not in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_VERIFICATION]:
            return Response(
                {"error": "Application is not in a claimable status."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Check claim conflict
        if application.claimed_by and application.claimed_by != request.user:
            if application.claimed_at and application.claimed_at >= thirty_min_ago:
                return Response(
                    {"error": f"Application is currently claimed by {application.claimed_by.full_name}"},
                    status=status.HTTP_409_CONFLICT
                )

        # 3, 4, 5. Update application
        application.claimed_by = request.user
        application.claimed_at = now
        if application.status == ApplicationStatus.SUBMITTED:
            application.status = ApplicationStatus.UNDER_VERIFICATION
        application.save()

        # 6. Log AuditLog
        from .models import AuditLog
        ip, ua = self._get_client_info(request)
        AuditLog.objects.create(
            entity_type="application",
            entity_id=application.id,
            application=application,
            action="claim",
            user=request.user,
            before_json={'claimed_by': None},
            after_json={'claimed_by': str(request.user.id)},
            ip_address=ip
        )

        # 7. Return detailed info
        serializer = self.get_serializer(application)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        application = self.get_object()

        # 1. Check ownership
        if application.claimed_by != request.user:
            return Response(
                {"error": "You do not have a claim on this application."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2, 3. Update application
        application.claimed_by = None
        application.claimed_at = None
        application.save()

        # 4. Log AuditLog
        from .models import AuditLog
        ip, ua = self._get_client_info(request)
        AuditLog.objects.create(
            entity_type="application",
            entity_id=application.id,
            application=application,
            action="release",
            user=request.user,
            before_json={'claimed_by': str(application.claimed_by_id) if application.claimed_by else None},
            after_json={'claimed_by': None},
            ip_address=ip
        )

        return Response({"message": "Application released back to queue."})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        from django.core.cache import cache
        cache_key = "verification:queue_stats"
        stats_data = cache.get(cache_key)

        thirty_min_ago = timezone.now() - timedelta(minutes=30)
        
        if not stats_data:
            # Base pending query (submitted or being verified)
            pending_apps = Application.objects.filter(
                status__in=[ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_VERIFICATION]
            )
            
            # Apps actually visible in queue (unclaimed or expired claim)
            queue_apps = pending_apps.filter(
                Q(claimed_by__isnull=True) |
                Q(claimed_at__lt=thirty_min_ago)
            ).annotate(
                avg_conf=Avg('student__documents__ocr_results__overall_confidence')
            )

            total_pending = pending_apps.count()
            
            # By Status
            by_status = {
                "submitted": pending_apps.filter(status=ApplicationStatus.SUBMITTED).count(),
                "under_verification": pending_apps.filter(status=ApplicationStatus.UNDER_VERIFICATION).count(),
            }
            
            # By Confidence
            high = queue_apps.filter(avg_conf__gte=0.90).count()
            medium = queue_apps.filter(avg_conf__gte=0.70, avg_conf__lt=0.90).count()
            low = queue_apps.filter(Q(avg_conf__lt=0.70) | Q(avg_conf__isnull=True)).count()
            
            # Average Confidence
            avg_val = queue_apps.aggregate(Avg('avg_conf'))['avg_conf__avg'] or 0.0
            
            # Oldest Pending
            oldest = pending_apps.order_by('submitted_at').filter(submitted_at__isnull=False).first()
            oldest_str = "N/A"
            if oldest and oldest.submitted_at:
                diff = timezone.now() - oldest.submitted_at
                if diff.days > 0:
                    oldest_str = f"{diff.days} days ago"
                else:
                    hours = diff.seconds // 3600
                    oldest_str = f"{hours} hours ago" if hours > 0 else "Just now"

            stats_data = {
                "total_pending": total_pending,
                "by_confidence": {
                    "high": high,
                    "medium": medium,
                    "low": low
                },
                "by_status": by_status,
                "oldest_pending": oldest_str,
                "average_confidence": round(avg_val, 2)
            }
            cache.set(cache_key, stats_data, timeout=30)

        # Add user-specific data (not cached globally)
        my_claimed = Application.objects.filter(
            claimed_by=request.user,
            claimed_at__gte=thirty_min_ago
        ).count()
        
        response_data = stats_data.copy()
        response_data["my_claimed"] = my_claimed
        
        return Response(response_data)

    @action(detail=False, methods=['get'], url_path='my-claims')
    def my_claims(self, request):
        """
        Returns list of applications currently claimed by the logged-in staff member.
        """
        thirty_min_ago = timezone.now() - timedelta(minutes=30)
        queryset = Application.objects.filter(
            claimed_by=request.user,
            claimed_at__gte=thirty_min_ago,
            status__in=[ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_VERIFICATION]
        ).select_related('student', 'student__user').prefetch_related(
            'student__documents', 
            'student__documents__ocr_results'
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SplitScreenViewSet(viewsets.GenericViewSet):
    """
    API endpoint for split-screen review of a single application.
    """
    permission_classes = [IsVerificationStaff]
    serializer_class = SplitScreenSerializer

    def get_queryset(self):
        # We don't need a queryset for single retrieve, but required for get_object
        return Application.objects.all()

    def get_object(self):
        """
        Retrieve application with claim validation.
        Staff must have claimed the application (unless admin).
        """
        app_id = self.kwargs.get('pk')
        try:
            application = Application.objects.select_related(
                'student', 'student__user'
            ).prefetch_related(
                'student__documents',
                'student__documents__ocr_results'
            ).get(id=app_id)
        except Application.DoesNotExist:
            raise Http404

        user = self.request.user
        # Admin can view any application
        if user.role == User.Role.ADMIN or user.is_superuser:
            return application

        # Staff must have claimed the application
        thirty_min_ago = timezone.now() - timedelta(minutes=30)
        if application.claimed_by != user or application.claimed_at < thirty_min_ago:
            raise PermissionDenied("You must have an active claim on this application.")

        return application

    def _get_client_info(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        return ip, user_agent

    def retrieve(self, request, *args, **kwargs):
        application = self.get_object()
        serializer = self.get_serializer(application)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='field')
    def field_edit(self, request, pk=None):
        """
        PATCH /api/verification/{app_id}/field/
        Update a single field value with audit trail.
        """
        # 1. Validate application access (staff must have claimed or be admin)
        application = self.get_object()

        # 2. Check application lock status
        is_allowed, error_response = check_application_lock(application, 'field_edit', request.user)
        if not is_allowed:
            return error_response

        # 3. Validate request data
        serializer = FieldEditRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 4. Get the document
        document_id = data.get('document_id')
        field_name = data.get('field_name')
        new_value = data.get('new_value', '')
        notes = data.get('notes', '')

        from documents.models import Document
        from .models import FieldVerification, FieldVerificationState, AuditLog

        try:
            document = Document.objects.get(id=document_id, student=application.student)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found for this application."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 5. Get the latest OCR result and its FieldVerification row
        ocr_result = document.get_latest_ocr_result()
        if not ocr_result:
            return Response(
                {"error": "No OCR result found for this document."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            field_verification = FieldVerification.objects.get(
                document=document,
                ocr_result=ocr_result,
                field_name=field_name
            )
        except FieldVerification.DoesNotExist:
            return Response(
                {"error": f"Field '{field_name}' not found in OCR results."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 6. Store old value and check if changed
        old_value = field_verification.current_value
        value_changed = old_value != new_value

        # 7. Update field verification
        if value_changed:
            field_verification.current_value = new_value
            field_verification.state = FieldVerificationState.EDITED
        field_verification.verified_by = request.user
        field_verification.verified_at = timezone.now()
        if notes:
            if field_verification.notes:
                field_verification.notes = f"{field_verification.notes}\n{notes}"
            else:
                field_verification.notes = notes
        field_verification.save()

        # 8. Create AuditLog
        ip, ua = self._get_client_info(request)
        AuditLog.objects.create(
            entity_type="field_verification",
            entity_id=field_verification.id,
            application=application,
            action="field_edit",
            user=request.user,
            field_name=field_name,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None,
            before_json={'current_value': str(old_value) if old_value else None},
            after_json={'current_value': str(new_value) if new_value else None, 'notes': notes},
            ip_address=ip
        )

        # 9. Return response
        response_serializer = FieldEditResponseSerializer(field_verification)
        return Response(response_serializer.data)

    @action(detail=True, methods=['post'], url_path='field/approve')
    def field_approve(self, request, pk=None):
        """
        POST /api/verification/{app_id}/field/approve/
        Mark a single field as approved without editing.
        """
        # 1. Validate application access
        application = self.get_object()

        if application.is_locked:
            return Response(
                {"error": "Application is locked. Cannot approve fields."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Validate request data
        serializer = FieldApproveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        document_id = data.get('document_id')
        field_name = data.get('field_name')

        from documents.models import Document
        from .models import FieldVerification, FieldVerificationState, AuditLog

        try:
            document = Document.objects.get(id=document_id, student=application.student)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found for this application."},
                status=status.HTTP_404_NOT_FOUND
            )

        ocr_result = document.get_latest_ocr_result()
        if not ocr_result:
            return Response(
                {"error": "No OCR result found for this document."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            field_verification = FieldVerification.objects.get(
                document=document,
                ocr_result=ocr_result,
                field_name=field_name
            )
        except FieldVerification.DoesNotExist:
            return Response(
                {"error": f"Field '{field_name}' not found in OCR results."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Update field verification
        old_state = field_verification.state
        field_verification.state = FieldVerificationState.APPROVED
        field_verification.verified_by = request.user
        field_verification.verified_at = timezone.now()
        field_verification.save()

        # 4. Create AuditLog
        ip, ua = self._get_client_info(request)
        AuditLog.objects.create(
            entity_type="field_verification",
            entity_id=field_verification.id,
            application=application,
            action="field_approve",
            user=request.user,
            field_name=field_name,
            old_value=old_state,
            new_value=FieldVerificationState.APPROVED,
            before_json={'state': old_state},
            after_json={'state': FieldVerificationState.APPROVED},
            ip_address=ip
        )

        # 5. Return response
        response_serializer = FieldApproveResponseSerializer(field_verification)
        return Response(response_serializer.data)

    @action(detail=True, methods=['post'], url_path='fields/approve-all')
    def fields_approve_all(self, request, pk=None):
        """
        POST /api/verification/{app_id}/fields/approve-all/
        Bulk approve all pending fields in a document.
        """
        # 1. Validate application access
        application = self.get_object()

        if application.is_locked:
            return Response(
                {"error": "Application is locked. Cannot approve fields."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Validate request data
        serializer = BulkApproveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        document_id = data.get('document_id')

        from documents.models import Document
        from .models import FieldVerification, FieldVerificationState, AuditLog

        try:
            document = Document.objects.get(id=document_id, student=application.student)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found for this application."},
                status=status.HTTP_404_NOT_FOUND
            )

        ocr_result = document.get_latest_ocr_result()
        if not ocr_result:
            return Response(
                {"error": "No OCR result found for this document."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get all pending field verifications
        pending_fields = FieldVerification.objects.filter(
            document=document,
            ocr_result=ocr_result,
            state=FieldVerificationState.PENDING
        )

        if not pending_fields.exists():
            return Response(
                {"message": "No pending fields to approve.", "approved_count": 0}
            )

        # 3. Approve all pending fields
        ip, ua = self._get_client_info(request)
        now = timezone.now()
        approved_count = 0

        for field_verification in pending_fields:
            old_state = field_verification.state
            field_verification.state = FieldVerificationState.APPROVED
            field_verification.verified_by = request.user
            field_verification.verified_at = now
            field_verification.save()

            # Create AuditLog for each field
            AuditLog.objects.create(
                entity_type="field_verification",
                entity_id=field_verification.id,
                application=application,
                action="field_approve",
                user=request.user,
                field_name=field_verification.field_name,
                old_value=old_state,
                new_value=FieldVerificationState.APPROVED,
                before_json={'state': old_state},
                after_json={'state': FieldVerificationState.APPROVED},
                ip_address=ip
            )
            approved_count += 1

        return Response({
            "message": f"Approved {approved_count} fields.",
            "approved_count": approved_count
        })

    @action(detail=True, methods=['post'], url_path='document/(?P<doc_id>[^/.]+)/verify')
    def document_verify(self, request, pk=None, doc_id=None):
        """
        POST /api/verification/{app_id}/document/{doc_id}/verify/
        Mark entire document as verified after all fields are reviewed.
        """
        # 1. Validate application access
        application = self.get_object()

        # 2. Check application lock status
        is_allowed, error_response = check_application_lock(application, 'verify_document', request.user)
        if not is_allowed:
            return error_response

        from documents.models import Document, DocumentStatus
        from .models import FieldVerification, FieldVerificationState, AuditLog

        # Get the document
        try:
            document = Document.objects.get(id=doc_id, student=application.student)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found for this application."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if already verified
        if document.status == DocumentStatus.VERIFIED:
            return Response(
                {"error": "Document already verified"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get latest OCR result
        ocr_result = document.get_latest_ocr_result()
        if not ocr_result:
            return Response(
                {"error": "No OCR result found for this document."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check all fields are reviewed (not pending)
        field_vers = FieldVerification.objects.filter(
            document=document,
            ocr_result=ocr_result
        )

        pending_fields = []
        verified_fields = []
        for fv in field_vers:
            if fv.state == FieldVerificationState.PENDING:
                pending_fields.append(fv.field_name)
            else:
                verified_fields.append(fv.field_name)

        # 2. Validate all fields are reviewed
        if pending_fields:
            return Response(
                {"error": f"Review all fields before verifying the document. {len(pending_fields)} pending."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Set document status to verified
        old_status = document.status
        document.status = DocumentStatus.VERIFIED
        document.save(update_fields=['status'])

        # 4. Create AuditLog
        ip, ua = self._get_client_info(request)
        AuditLog.objects.create(
            entity_type="document",
            entity_id=document.id,
            application=application,
            action="document_verify",
            user=request.user,
            old_value=old_status,
            new_value=DocumentStatus.VERIFIED,
            before_json={'status': old_status},
            after_json={'status': DocumentStatus.VERIFIED},
            ip_address=ip
        )

        # 5. Return response
        response_data = {
            "document_id": document.id,
            "document_type": document.document_type,
            "status": document.status,
            "verified_fields": verified_fields,
            "pending_fields": pending_fields
        }
        return Response(response_data)

    @action(detail=True, methods=['post'], url_path='document/(?P<doc_id>[^/.]+)/reject')
    def document_reject(self, request, pk=None, doc_id=None):
        """
        POST /api/verification/{app_id}/document/{doc_id}/reject/
        Reject a document and request re-upload.
        """
        # 1. Validate application access
        application = self.get_object()

        # 2. Check application lock status
        is_allowed, error_response = check_application_lock(application, 'reject_document', request.user)
        if not is_allowed:
            return error_response

        # 2. Validate request data
        serializer = DocumentRejectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from documents.models import Document, DocumentStatus
        from .models import FieldVerification, FieldVerificationState, AuditLog

        # 3. Get the document
        try:
            document = Document.objects.get(id=doc_id, student=application.student)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found for this application."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if already verified
        if document.status == DocumentStatus.VERIFIED:
            return Response(
                {"error": "Cannot reject a verified document."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Update document with rejection details
        now = timezone.now()
        old_status = document.status

        with transaction.atomic():
            document.status = DocumentStatus.REJECTED
            document.rejection_reason = data.get('rejection_reason')
            document.rejection_category = data.get('rejection_category')
            document.rejected_by = request.user
            document.rejected_at = now
            document.reupload_requested_at = now
            document.reupload_count = (document.reupload_count or 0) + 1
            document.save()

            # 5. Update parent Application status if submitted
            if application.status == ApplicationStatus.SUBMITTED:
                application.status = ApplicationStatus.UNDER_VERIFICATION
                application.save(update_fields=['status'])

            # 6. Mark all FieldVerification rows as flagged
            ocr_result = document.get_latest_ocr_result()
            if ocr_result:
                FieldVerification.objects.filter(
                    document=document,
                    ocr_result=ocr_result
                ).update(
                    state=FieldVerificationState.FLAGGED,
                    verified_by=request.user,
                    verified_at=now
                )

            # 7. Write AuditLog entry
            ip, ua = self._get_client_info(request)
            AuditLog.objects.create(
                entity_type="document",
                entity_id=document.id,
                application=application,
                action="reject_doc",
                user=request.user,
                old_value=old_status,
                new_value=DocumentStatus.REJECTED,
                before_json={'status': old_status},
                after_json={'status': DocumentStatus.REJECTED, 'rejection_reason': data.get('rejection_reason'), 'rejection_category': data.get('rejection_category')},
                ip_address=ip
            )

        # 8. Trigger Celery task if notify_student is True
        notify_student = data.get('notify_student', True)
        if notify_student:
            try:
                from notifications.tasks import send_notification
                from django.conf import settings
                
                send_notification.delay(
                    notification_type='document_reupload_request',
                    user_id=str(document.student.user_id),
                    context={
                        'email': document.student.user.email,
                        'document_type': document.get_document_type_display(),
                        'rejection_category_label': document.get_rejection_category_display(),
                        'rejection_reason': document.rejection_reason,
                        'reason_preview': document.rejection_reason[:80] if document.rejection_reason else '',
                        'reupload_link': f'{settings.MOBILE_APP_SCHEME}://documents/rejected',
                        'application_number': document.student.application.application_number,
                        'related_object_id': str(document.id),
                    },
                )
            except Exception:
                pass

        # 9. Return updated document payload
        response_data = {
            "document_id": document.id,
            "document_type": document.document_type,
            "status": document.status,
            "rejection_reason": document.rejection_reason,
            "rejection_category": document.rejection_category,
            "reupload_requested_at": document.reupload_requested_at,
            "reupload_count": document.reupload_count
        }
        return Response(response_data)

    @action(detail=False, methods=['post'], url_path='documents/(?P<doc_id>[^/.]+)/withdraw-rejection')
    def withdraw_rejection(self, request, doc_id=None):
        """
        POST /api/verification/documents/{doc_id}/withdraw-rejection/
        Withdraw a document rejection before student re-uploads.
        """
        from documents.models import Document, DocumentStatus
        from .models import AuditLog

        # Get the document
        try:
            document = Document.objects.get(id=doc_id)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get the application and validate claim
        application = document.student.application_set.first()
        if not application:
            return Response(
                {"error": "Application not found for this document."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check claim ownership
        thirty_min_ago = timezone.now() - timedelta(minutes=30)
        user = request.user
        if user.role != User.Role.ADMIN and user.role != User.Role.VERIFICATION_STAFF:
            return Response(
                {"error": "Only verification staff can withdraw rejections."},
                status=status.HTTP_403_FORBIDDEN
            )

        if application.claimed_by != user or application.claimed_at < thirty_min_ago:
            return Response(
                {"error": "You must have an active claim on this application."},
                status=status.HTTP_403_FORBIDDEN
            )

        if document.status != DocumentStatus.REJECTED:
            return Response(
                {"error": "Document is not in rejected status."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Store old values for audit
        old_status = document.status

        # Clear rejection fields and set status back to extracted
        with transaction.atomic():
            document.status = DocumentStatus.EXTRACTED
            document.rejection_reason = None
            document.rejection_category = None
            document.rejected_by = None
            document.rejected_at = None
            document.reupload_requested_at = None
            document.save()

            # Create AuditLog entry
            ip, ua = self._get_client_info(request)
            AuditLog.objects.create(
                entity_type="document",
                entity_id=document.id,
                application=application,
                action="withdraw_rejection",
                user=request.user,
                old_value=old_status,
                new_value=DocumentStatus.EXTRACTED,
                before_json={'status': old_status},
                after_json={'status': DocumentStatus.EXTRACTED},
                ip_address=ip
            )

        response_data = {
            "document_id": document.id,
            "document_type": document.document_type,
            "status": document.status,
            "message": "Rejection withdrawn successfully."
        }
        return Response(response_data)


class DocumentReuploadHistoryViewSet(viewsets.GenericViewSet):
    """
    API endpoint for document reupload history.
    Returns chronological list of events: upload -> rejection -> re-upload -> OCR result -> rejection...
    """
    permission_classes = [IsVerificationStaff]
    serializer_class = ReuploadHistoryEventSerializer

    def get_queryset(self):
        return None

    def get_object(self):
        from documents.models import Document
        doc_id = self.kwargs.get('pk')
        try:
            return Document.objects.select_related('student', 'student__user').get(id=doc_id)
        except Document.DoesNotExist:
            raise Http404

    def retrieve(self, request, *args, **kwargs):
        document = self.get_object()
        events = self._build_history(document)
        serializer = self.serializer_class(events, many=True)
        return Response(serializer.data)

    def _build_history(self, document):
        events = []
        
        # Get all OCR results for this document (ordered by version ascending)
        ocr_results = document.ocr_results.order_by('ocr_version')
        
        # Track rejection events from audit logs
        from .models import AuditLog
        rejection_logs = AuditLog.objects.filter(
            entity_type='document',
            entity_id=document.id,
            action__in=['reject_doc', 'withdraw_rejection']
        ).order_by('timestamp')

        rejection_by_version = {}
        for log in rejection_logs:
            if log.action == 'reject_doc':
                rejection_by_version[document.upload_version] = {
                    'timestamp': log.timestamp,
                    'actor': log.user.email if log.user else 'System',
                    'reason': log.new_value,
                    'category': log.field_name
                }
            elif log.action == 'withdraw_rejection':
                if document.upload_version in rejection_by_version:
                    del rejection_by_version[document.upload_version]

        # Build events from upload version 1 to current
        for version in range(1, document.upload_version + 1):
            # Upload event
            upload_time = document.uploaded_at
            if version > 1:
                upload_time = document.uploaded_at
            
            events.append({
                'event_type': 'upload',
                'timestamp': upload_time,
                'details': {
                    'version': version,
                    'file_name': document.file_name,
                    'mime_type': document.mime_type
                },
                'actor': document.uploaded_by.email if document.uploaded_by else 'Student',
                'version': version
            })

            # Check for rejection at this version
            if version in rejection_by_version:
                rejection = rejection_by_version[version]
                events.append({
                    'event_type': 'rejection',
                    'timestamp': rejection['timestamp'],
                    'details': {
                        'reason': rejection['reason'],
                        'category': rejection.get('category', 'unknown')
                    },
                    'actor': rejection['actor'],
                    'version': version
                })

            # OCR result for this version
            ocr = ocr_results.filter(ocr_version=version).first()
            if ocr:
                events.append({
                    'event_type': 'ocr_complete',
                    'timestamp': ocr.created_at,
                    'details': {
                        'overall_confidence': ocr.overall_confidence,
                        'field_count': len(ocr.extracted_fields) if ocr.extracted_fields else 0,
                        'llm_model': ocr.llm_model_used
                    },
                    'actor': 'System',
                    'version': version
                })

        # Sort all events by timestamp
        events.sort(key=lambda x: x['timestamp'])
        
        return events


class ApplicationAuditLogsViewSet(viewsets.GenericViewSet):
    """
    API endpoint for retrieving audit logs for an application.
    GET /api/verification/applications/{app_id}/audit-logs/
    """
    permission_classes = [IsVerificationStaff]
    serializer_class = None

    def get_queryset(self):
        return None

    def get_object(self):
        from admissions.models import Application
        app_id = self.kwargs.get('pk')
        try:
            return Application.objects.get(id=app_id)
        except Application.DoesNotExist:
            raise Http404

    def retrieve(self, request, *args, **kwargs):
        application = self.get_object()
        
        logs = AuditLog.objects.filter(
            application=application
        ).select_related('user').order_by('-timestamp')[:100]
        
        data = []
        for log in logs:
            data.append({
                'id': str(log.id),
                'entity_type': log.entity_type,
                'entity_id': str(log.entity_id),
                'action': log.action,
                'user': {
                    'id': str(log.user.id) if log.user else None,
                    'email': log.user.email if log.user else None,
                } if log.user else None,
                'before_json': log.before_json,
                'after_json': log.after_json,
                'ip_address': log.ip_address,
                'timestamp': log.timestamp.isoformat(),
            })
        
        return Response(data)
