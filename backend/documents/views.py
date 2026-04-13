from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from .models import Document, OCRResult, DocumentStatus
from .serializers import (
    DocumentListSerializer,
    DocumentDetailSerializer,
    DocumentUploadSerializer,
    DocumentReuploadSerializer,
    OCRResultDetailSerializer,
    OCRResultHistorySerializer,
)
from .utils import save_document
from .services.ocr_service import process_document
from .services.ocr_exceptions import (
    OCRProcessingError,
    OCREmptyResultError,
    DocumentValidationError,
)
from django.conf import settings
from django.core.cache import cache
import os

from admissions.models import ApplicationStatus

OCR_PROCESSING_TTL_SECONDS = 300


def _is_reupload_allowed(user, document: Document) -> bool:
    is_owner_student = (
        user.role == "student"
        and hasattr(user, "student_profile")
        and document.student_id == user.student_profile.id
    )
    is_agent_uploader = user.role == "agent" and document.uploaded_by_id == user.id
    return is_owner_student or is_agent_uploader or user.is_superuser


def _can_access_document(user, document: Document) -> bool:
    is_owner_student = (
        user.role == "student"
        and hasattr(user, "student_profile")
        and document.student_id == user.student_profile.id
    )
    is_agent_for_student = (
        user.role == "agent"
        and document.student.agent_id is not None
        and document.student.agent.user_id == user.id
    )
    is_staff = user.role in ["verification_staff", "admission_officer", "admin"]
    return is_owner_student or is_agent_for_student or is_staff or user.is_superuser


def _build_upload_response(document: Document, ocr_result: OCRResult | None, ocr_warning: str | None):
    payload = {
        "id": str(document.id),
        "document_type": document.document_type,
        "status": document.status,
        "upload_version": document.upload_version,
        "ocr_result": None,
    }
    if ocr_result is not None:
        payload["ocr_result"] = {
            "extracted_fields": ocr_result.extracted_fields,
            "confidence_scores": ocr_result.confidence_scores,
            "overall_confidence": ocr_result.overall_confidence,
            "processing_duration_ms": ocr_result.processing_duration_ms,
        }
    elif ocr_warning:
        payload["ocr_warning"] = ocr_warning
    return payload


def _run_sync_ocr(document: Document):
    ocr_result = None
    ocr_warning = None
    try:
        ocr_result = process_document(document.id)
        document.refresh_from_db(fields=["status", "upload_version"])
    except OCREmptyResultError:
        document.refresh_from_db(fields=["status", "upload_version"])
        ocr_warning = "OCR returned empty result, please fill fields manually"
    except OCRProcessingError:
        document.refresh_from_db(fields=["status", "upload_version"])
        ocr_warning = "OCR processing failed, please fill fields manually"
    return ocr_result, ocr_warning


def _ocr_lock_key(document_id) -> str:
    return f"ocr:processing:{document_id}"


def _is_ocr_in_progress(document_id) -> bool:
    return cache.get(_ocr_lock_key(document_id)) is not None


def _set_ocr_in_progress(document_id):
    cache.set(_ocr_lock_key(document_id), "in_progress", timeout=OCR_PROCESSING_TTL_SECONDS)


def _clear_ocr_in_progress(document_id):
    cache.delete(_ocr_lock_key(document_id))


class DocumentUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not hasattr(request.user, "student_profile"):
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student_profile = request.user.student_profile
        upload_file = serializer.validated_data["file"]
        document_type = serializer.validated_data["document_type"]
        existing_document = Document.objects.filter(
            student=student_profile, document_type=document_type
        ).first()

        application = getattr(student_profile, "application", None)
        is_application_locked = (
            application is not None
            and application.status != ApplicationStatus.DRAFT
        )
        if existing_document and is_application_locked:
            return Response(
                {
                    "error": (
                        "Documents are locked after submission. "
                        "Re-upload is allowed only for rejected documents."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if existing_document and _is_ocr_in_progress(existing_document.id):
            return Response(
                {"error": "Document is already being processed"},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            file_path = save_document(student_profile.id, document_type, upload_file)
        except DocumentValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        document = existing_document
        if document:
            document.file_path = file_path
            document.file_name = upload_file.name
            document.file_size_bytes = upload_file.size
            document.mime_type = (
                upload_file.content_type or "application/octet-stream"
            )
            document.upload_version += 1
            document.status = DocumentStatus.PROCESSING
            document.rejection_reason = None
            document.uploaded_by = request.user
            document.save(
                update_fields=[
                    "file_path",
                    "file_name",
                    "file_size_bytes",
                    "mime_type",
                    "upload_version",
                    "status",
                    "rejection_reason",
                    "uploaded_by",
                ]
            )
        else:
            document = Document.objects.create(
                student=student_profile,
                document_type=document_type,
                file_path=file_path,
                file_name=upload_file.name,
                file_size_bytes=upload_file.size,
                mime_type=upload_file.content_type or "application/octet-stream",
                upload_version=1,
                status=DocumentStatus.PROCESSING,
                uploaded_by=request.user,
            )

        _set_ocr_in_progress(document.id)
        try:
            ocr_result, ocr_warning = _run_sync_ocr(document)
        finally:
            _clear_ocr_in_progress(document.id)
        payload = _build_upload_response(document, ocr_result, ocr_warning)

        return Response(payload, status=status.HTTP_201_CREATED)


class DocumentReuploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from django.db import transaction
        from django.utils import timezone
        from verification.models import FieldVerification, AuditLog

        document = get_object_or_404(Document, pk=pk)

        if not _is_reupload_allowed(request.user, document):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        if document.status != DocumentStatus.REJECTED:
            return Response(
                {"error": "Only rejected documents can be re-uploaded"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if _is_ocr_in_progress(document.id):
            return Response(
                {"error": "Document is already being processed"},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = DocumentReuploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload_file = serializer.validated_data["file"]

        old_file_path = document.file_path
        old_status = document.status

        try:
            file_path = save_document(document.student_id, document.document_type, upload_file)
        except DocumentValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            document.file_path = file_path
            document.file_name = upload_file.name
            document.file_size_bytes = upload_file.size
            document.mime_type = upload_file.content_type or "application/octet-stream"
            document.upload_version += 1
            document.status = DocumentStatus.PROCESSING
            document.rejection_reason = None
            document.rejection_category = None
            document.rejected_by = None
            document.rejected_at = None
            document.reupload_count = (document.reupload_count or 0) + 1
            document.uploaded_by = request.user
            document.save(
                update_fields=[
                    "file_path",
                    "file_name",
                    "file_size_bytes",
                    "mime_type",
                    "upload_version",
                    "status",
                    "rejection_reason",
                    "rejection_category",
                    "rejected_by",
                    "rejected_at",
                    "reupload_count",
                    "uploaded_by",
                ]
            )

            latest_ocr = document.get_latest_ocr_result()
            if latest_ocr:
                FieldVerification.objects.filter(
                    document=document,
                    ocr_result=latest_ocr
                ).update(is_superseded=True)

            ip = request.META.get("REMOTE_ADDR")
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            AuditLog.objects.create(
                user=request.user,
                application=document.student.application_set.first(),
                action="reupload",
                entity_type="document",
                entity_id=document.id,
                old_value=old_status,
                new_value=DocumentStatus.PROCESSING,
                ip_address=ip,
                user_agent=user_agent,
            )

        _set_ocr_in_progress(document.id)
        try:
            ocr_result, ocr_warning = _run_sync_ocr(document)
        finally:
            _clear_ocr_in_progress(document.id)

        document.refresh_from_db()

        return Response({
            "id": str(document.id),
            "status": document.status,
            "reupload_count": document.reupload_count,
            "ocr_result_id": str(ocr_result.id) if ocr_result else None,
            "overall_confidence": ocr_result.overall_confidence if ocr_result else None,
        }, status=status.HTTP_200_OK)


class DocumentListView(generics.ListAPIView):
    serializer_class = DocumentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return Document.objects.filter(student=user.student_profile)
        elif user.role == 'agent':
            student_id = self.request.query_params.get('student_id')
            return Document.objects.filter(student_id=student_id, student__agent__user=user)
        return Document.objects.all()

class DocumentDetailView(generics.RetrieveAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentFileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)

        if not _can_access_document(request.user, doc):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        file_path = os.path.join(settings.MEDIA_ROOT, doc.file_path)
        return FileResponse(open(file_path, 'rb'), content_type=doc.mime_type)


class DocumentOCRResultView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        if not _can_access_document(request.user, document):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        latest = document.get_latest_ocr_result()
        if not latest:
            return Response({"error": "OCR result not found"}, status=status.HTTP_404_NOT_FOUND)

        data = OCRResultDetailSerializer(latest).data
        return Response(data, status=status.HTTP_200_OK)


class DocumentOCRHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        if not _can_access_document(request.user, document):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        history_qs = document.get_ocr_history()
        data = OCRResultHistorySerializer(history_qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)
