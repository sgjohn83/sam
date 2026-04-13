from uuid import UUID

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from admissions.models import ApplicationStatus
from documents.models import Document, DocumentStatus, DocumentType
from documents.services.application_autofill import generate_autofill_data
from .serializers import StudentProfileSerializer
from .models import PushToken, StudentProfile


REQUIRED_DOCUMENT_TYPES = [
    DocumentType.AADHAR,
    DocumentType.MARKSHEET_10,
    DocumentType.MARKSHEET_12,
    DocumentType.RANK_CARD,
]


def _is_profile_locked(profile: StudentProfile) -> bool:
    application = getattr(profile, "application", None)
    if application is None:
        return False
    return application.is_locked or application.status != ApplicationStatus.DRAFT


def _profile_response_payload(profile: StudentProfile) -> dict:
    return {
        "id": str(profile.id),
        "full_name": profile.user.full_name,
        "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
        "gender": profile.gender,
        "mobile_number": profile.mobile_number,
        "address": profile.address,
        "category": profile.category,
        "domicile_state": profile.domicile_state,
        "application_status": getattr(profile.application, "status", ApplicationStatus.DRAFT),
    }


class StudentAutofillView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Student: own data only
        if request.user.role == User.Role.STUDENT:
            if not hasattr(request.user, "student_profile"):
                return Response(
                    {"error": "Student profile not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            payload = generate_autofill_data(request.user.student_profile.id)
            return Response(payload, status=status.HTTP_200_OK)

        # Admin / superuser: can request a specific student_id
        if request.user.role == User.Role.ADMIN or request.user.is_superuser:
            student_id = request.query_params.get("student_id")
            if not student_id:
                return Response(
                    {"error": "student_id is required for admin access"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                student_uuid = UUID(student_id)
            except ValueError:
                return Response(
                    {"error": "Invalid student_id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not StudentProfile.objects.filter(id=student_uuid).exists():
                return Response(
                    {"error": "Student profile not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            payload = generate_autofill_data(student_uuid)
            return Response(payload, status=status.HTTP_200_OK)

        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)


class StudentProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            _profile_response_payload(request.user.student_profile),
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        if hasattr(request.user, "student_profile"):
            return Response(
                {"error": "Student profile already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = StudentProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save(user=request.user)

        full_name = request.data.get("full_name")
        if isinstance(full_name, str) and full_name.strip():
            request.user.full_name = full_name.strip()
            request.user.save(update_fields=["full_name"])

        return Response(_profile_response_payload(profile), status=status.HTTP_201_CREATED)

    def put(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        profile = request.user.student_profile
        if _is_profile_locked(profile):
            return Response(
                {"error": "Profile locked after submission"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = StudentProfileSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        full_name = request.data.get("full_name")
        if isinstance(full_name, str) and full_name.strip():
            request.user.full_name = full_name.strip()
            request.user.save(update_fields=["full_name"])

        return Response(_profile_response_payload(profile), status=status.HTTP_200_OK)


class StudentProfileCompletionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response(
                {
                    "is_complete": False,
                    "application_status": ApplicationStatus.DRAFT,
                    "documents_complete": False,
                    "documents": {
                        "uploaded_count": 0,
                        "required_count": len(REQUIRED_DOCUMENT_TYPES),
                        "items": [],
                    },
                },
                status=status.HTTP_200_OK,
            )

        profile = request.user.student_profile
        docs = Document.objects.filter(student=profile)
        docs_by_type = {doc.document_type: doc for doc in docs}

        missing_fields = []
        if not (profile.user.full_name or "").strip():
            missing_fields.append("full_name")
        if not profile.date_of_birth:
            missing_fields.append("date_of_birth")
        if not profile.gender:
            missing_fields.append("gender")
        if not (profile.mobile_number or "").strip():
            missing_fields.append("mobile_number")
        if not profile.address:
            missing_fields.append("address")
        if not profile.category:
            missing_fields.append("category")
        if not (profile.domicile_state or "").strip():
            missing_fields.append("domicile_state")

        items = []
        uploaded_count = 0
        for doc_type in REQUIRED_DOCUMENT_TYPES:
            doc = docs_by_type.get(doc_type)
            if doc is not None:
                uploaded_count += 1
            items.append(
                {
                    "document_type": doc_type,
                    "uploaded": doc is not None,
                    "status": doc.status if doc else None,
                }
            )

        return Response(
            {
                "is_complete": len(missing_fields) == 0,
                "missing_fields": missing_fields,
                "application_status": getattr(profile.application, "status", ApplicationStatus.DRAFT),
                "documents_complete": uploaded_count == len(REQUIRED_DOCUMENT_TYPES),
                "documents": {
                    "uploaded_count": uploaded_count,
                    "required_count": len(REQUIRED_DOCUMENT_TYPES),
                    "items": items,
                },
            },
            status=status.HTTP_200_OK,
        )


class StudentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"application_status": ApplicationStatus.DRAFT},
                status=status.HTTP_200_OK,
            )

        profile = request.user.student_profile
        application = getattr(profile, "application", None)

        rejected_doc = (
            Document.objects.filter(student=profile, status=DocumentStatus.REJECTED)
            .order_by("-uploaded_at")
            .first()
        )

        response = {
            "application_status": application.status if application else ApplicationStatus.DRAFT,
            "action_required": rejected_doc is not None,
            "rejected_document": None,
            "seat_allocated": bool(application and application.allocated_branch_id),
            "seat_details": None,
        }

        if rejected_doc is not None:
            response["rejected_document"] = {
                "document_type": rejected_doc.document_type,
                "document_name": rejected_doc.get_document_type_display(),
                "reason": rejected_doc.rejection_reason,
            }

        if application and application.allocated_branch_id:
            response["seat_details"] = {
                "branch": application.allocated_branch.name,
                "quota": application.allocated_quota,
                "fee_amount": str(application.fee_amount) if application.fee_amount is not None else None,
                "deadline": None,
            }

        return Response(response, status=status.HTTP_200_OK)


class StudentPushTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get("token")
        platform = str(request.data.get("platform", "")).lower()

        if not token:
            return Response(
                {"error": "token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if platform not in {PushToken.Platform.IOS, PushToken.Platform.ANDROID}:
            return Response(
                {"error": "platform must be ios or android"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        push_token, created = PushToken.objects.get_or_create(
            user=request.user,
            token=token,
            defaults={"platform": platform},
        )
        if not created and push_token.platform != platform:
            push_token.platform = platform
            push_token.save(update_fields=["platform"])

        return Response({"message": "Push token saved"}, status=status.HTTP_201_CREATED)


class StudentRejectedDocumentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"error": "Student profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        profile = request.user.student_profile
        rejected_docs = Document.objects.filter(
            student=profile,
            status=DocumentStatus.REJECTED
        ).order_by("-rejected_at")

        results = []
        for doc in rejected_docs:
            results.append({
                "id": str(doc.id),
                "document_type": doc.document_type,
                "document_type_label": doc.get_document_type_display(),
                "rejection_reason": doc.rejection_reason,
                "rejection_category": doc.rejection_category,
                "rejection_category_display": doc.get_rejection_category_display() if doc.rejection_category else None,
                "rejected_at": doc.rejected_at.isoformat() if doc.rejected_at else None,
                "reupload_requested_at": doc.reupload_requested_at.isoformat() if doc.reupload_requested_at else None,
                "reupload_count": doc.reupload_count,
                "original_file_url": f"/api/documents/{doc.id}/file/",
            })

        return Response({
            "count": len(results),
            "documents": results
        }, status=status.HTTP_200_OK)


class RejectedDocumentsCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.core.cache import cache
        
        cache_key = f"rejected_count:{request.user.id}"
        cached_count = cache.get(cache_key)
        
        if cached_count is not None:
            return Response({"count": cached_count})
        
        if not hasattr(request.user, "student_profile"):
            return Response({"count": 0})
        
        count = Document.objects.filter(
            student=request.user.student_profile,
            status=DocumentStatus.REJECTED,
        ).count()
        
        cache.set(cache_key, count, timeout=30)
        
        return Response({"count": count})
