from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Sum

from accounts.models import User
from administration.models import AcademicYear, Branch, QuotaType, SeatMatrix
from admissions.models import Application, ApplicationStatus
from .engine import allocate_seat, deallocate_seat, SeatUnavailableError, SeatAlreadyAllocatedError


SEATS_CACHE_TTL = 10


class SeatAvailabilityView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return Response(
                {"error": "No current academic year"},
                status=status.HTTP_400_BAD_REQUEST
            )

        branches = Branch.objects.filter(is_active=True).order_by("name")
        
        result = []
        for branch in branches:
            quotas_data = []
            
            for quota, quota_label in QuotaType.choices:
                cache_key = f"seats:{branch.id}:{quota}"
                cached = cache.get(cache_key)
                
                if cached is None:
                    sm = SeatMatrix.objects.filter(
                        academic_year=current_year,
                        branch=branch,
                        quota=quota,
                    ).first()
                    
                    total = sm.total_seats if sm else 0
                    allocated = sm.allocated_seats if sm else 0
                    available = max(total - allocated, 0)
                    
                    cached = {
                        "total": total,
                        "allocated": allocated,
                        "available": available,
                    }
                    cache.set(cache_key, cached, timeout=SEATS_CACHE_TTL)
                
                quotas_data.append({
                    "quota": quota,
                    "quota_label": quota_label,
                    "total": cached["total"],
                    "allocated": cached["allocated"],
                    "available": cached["available"],
                })
            
            result.append({
                "branch_id": str(branch.id),
                "branch_name": branch.name,
                "branch_code": branch.code,
                "quotas": quotas_data,
            })
        
        return Response(result, status=status.HTTP_200_OK)


class SeatAvailabilitySummaryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return Response(
                {"error": "No current academic year"},
                status=status.HTTP_400_BAD_REQUEST
            )

        summary_cache_key = "seats:summary"
        cached = cache.get(summary_cache_key)
        
        if cached is None:
            totals = SeatMatrix.objects.filter(
                academic_year=current_year,
            ).aggregate(
                total_seats=Sum("total_seats"),
                allocated_seats=Sum("allocated_seats"),
            )
            
            total = totals["total_seats"] or 0
            allocated = totals["allocated_seats"] or 0
            available = max(total - allocated, 0)
            fill_percentage = round((allocated / total * 100), 1) if total > 0 else 0
            
            cached = {
                "total_seats": total,
                "allocated_seats": allocated,
                "available_seats": available,
                "fill_percentage": fill_percentage,
            }
            cache.set(summary_cache_key, cached, timeout=SEATS_CACHE_TTL)
        
        return Response(cached, status=status.HTTP_200_OK)


class OfficerAllocateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not request.user.role in [User.Role.ADMIN, User.Role.OFFICER]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response(
                {"error": "Application not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if application.allocated_branch_id:
            return Response(
                {"error": f"Application already allocated to {application.allocated_branch.name}", "code": "ALREADY_ALLOCATED"},
                status=status.HTTP_409_CONFLICT
            )

        if application.status not in [ApplicationStatus.VERIFIED, ApplicationStatus.UNDER_VERIFICATION]:
            return Response(
                {"error": f"Application must be verified or under verification, current: {application.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        branch_id = request.data.get("branch_id")
        quota = request.data.get("quota")
        force = request.data.get("force", False)

        if not branch_id or not quota:
            return Response(
                {"error": "branch_id and quota are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            branch = Branch.objects.get(pk=branch_id, is_active=True)
        except Branch.DoesNotExist:
            return Response(
                {"error": "Invalid branch_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quota not in QuotaType.values:
            return Response(
                {"error": "Invalid quota"},
                status=status.HTTP_400_BAD_REQUEST
            )

        branch_prefs = application.branch_preferences or []
        if str(branch_id) not in branch_prefs and not force:
            return Response(
                {"warning": f"Branch {branch.name} not in student's preferences"},
                status=status.HTTP_400_BAD_REQUEST
            )

        student_category = getattr(application.student, "category", None)
        if student_category and not _is_eligible_for_quota(student_category, quota):
            return Response(
                {"error": f"Student category {student_category} not eligible for quota {quota}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            allocate_seat(application.id, branch_id, quota, actor=request.user)
        except SeatUnavailableError as e:
            return Response(
                {"error": str(e), "code": "NO_SEATS"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except SeatAlreadyAllocatedError as e:
            return Response(
                {"error": str(e), "code": "ALREADY_ALLOCATED"},
                status=status.HTTP_409_CONFLICT
            )

        application.refresh_from_db()

        seat_row = SeatMatrix.objects.filter(
            academic_year=AcademicYear.objects.filter(is_current=True).first(),
            branch=branch,
            quota=quota,
        ).first()

        return Response({
            "application": {
                "id": str(application.id),
                "application_number": application.application_number,
                "status": application.status,
                "allocated_branch": branch.name,
                "allocated_quota": quota,
            },
            "seat_availability": {
                "total": seat_row.total_seats if seat_row else 0,
                "allocated": seat_row.allocated_seats if seat_row else 0,
                "available": max(seat_row.total_seats - seat_row.allocated_seats, 0) if seat_row else 0,
            },
        }, status=status.HTTP_200_OK)


class OfficerDeallocateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not request.user.role in [User.Role.ADMIN, User.Role.OFFICER]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        reason = request.data.get("reason", "").strip()
        if len(reason) < 10:
            return Response(
                {"error": "Reason (min 10 chars) is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response(
                {"error": "Application not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not application.allocated_branch_id:
            return Response(
                {"error": "No seat allocated to this application"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            deallocate_seat(application.id, actor=request.user, reason=reason)
        except SeatUnavailableError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

        application.refresh_from_db()

        return Response({
            "application": {
                "id": str(application.id),
                "application_number": application.application_number,
                "status": application.status,
                "allocated_branch": None,
                "allocated_quota": None,
            },
            "message": "Seat deallocated successfully",
        }, status=status.HTTP_200_OK)


class OfficerBulkAllocateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.role in [User.Role.ADMIN, User.Role.OFFICER]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        items = request.data.get("items", [])
        if not items:
            return Response(
                {"error": "items array is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(items) > 50:
            return Response(
                {"error": "Maximum 50 items per batch"},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        current_year = AcademicYear.objects.filter(is_current=True).first()

        try:
            with transaction.atomic():
                for idx, item in enumerate(items):
                    item_result = {"index": idx, "application_id": str(item["application_id"]), "success": False}
                    try:
                        app_id = item["application_id"]
                        branch_id = item["branch_id"]
                        quota = item["quota"]

                        application = Application.objects.get(pk=app_id)

                        if application.allocated_branch_id:
                            item_result["error"] = "Already allocated"
                            results.append(item_result)
                            continue

                        branch_prefs = application.branch_preferences or []
                        if str(branch_id) not in branch_prefs:
                            item_result["error"] = "Branch not in preferences"
                            results.append(item_result)
                            raise Exception("rollback")

                        seat_row = SeatMatrix.objects.select_for_update().filter(
                            academic_year=current_year,
                            branch_id=branch_id,
                            quota=quota,
                        ).first()

                        if not seat_row or seat_row.allocated_seats >= seat_row.total_seats:
                            item_result["error"] = "No seats available"
                            results.append(item_result)
                            raise Exception("rollback")

                        allocate_seat(app_id, branch_id, quota, actor=request.user)
                        item_result["success"] = True

                    except Application.DoesNotExist:
                        item_result["error"] = "Application not found"
                    except KeyError:
                        item_result["error"] = "Missing required fields"
                    except Exception as e:
                        if str(e) == "rollback":
                            transaction.setrollback(True)
                            break
                        item_result["error"] = str(e)

                    results.append(item_result)

        except Exception:
            pass

        success_count = sum(1 for r in results if r["success"])
        return Response({
            "total": len(items),
            "succeeded": success_count,
            "failed": len(items) - success_count,
            "results": results,
        }, status=status.HTTP_200_OK)


def _is_eligible_for_quota(category, quota):
    """Check if category is eligible for quota."""
    eligible = {
        "general": ["general"],
        "obc": ["general", "obc"],
        "sc": ["general", "obc", "sc"],
        "st": ["general", "obc", "sc", "st"],
        "management": ["general", "management"],
        "nri": ["general", "nri"],
    }
    return category in eligible.get(quota, [])


class OfficerAllocationSuggestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.role in [User.Role.ADMIN, User.Role.OFFICER]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        branch_id = request.query_params.get("branch_id")
        quota = request.query_params.get("quota")
        limit = min(int(request.query_params.get("limit", 10)), 50)

        if not branch_id or not quota:
            return Response(
                {"error": "branch_id and quota are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return Response(
                {"error": "No current academic year"},
                status=status.HTTP_400_BAD_REQUEST
            )

        seat_row = SeatMatrix.objects.filter(
            academic_year=current_year,
            branch_id=branch_id,
            quota=quota,
        ).first()

        available = 0
        if seat_row:
            available = max(seat_row.total_seats - seat_row.allocated_seats, 0)

        branch_prefs = Application.objects.filter(
            status__in=[ApplicationStatus.VERIFIED, ApplicationStatus.UNDER_VERIFICATION],
            allocated_branch__isnull=True,
        ).filter(
            branch_preferences__contains=[str(branch_id)]
        ).order_by("-fee_amount", "submitted_at")

        candidates = []
        for idx, app in enumerate(branch_prefs[:limit + available]):
            student = app.student
            category = getattr(student, "category", None)
            if not _is_eligible_for_quota(category, quota):
                continue

            pref_order = None
            prefs = app.branch_preferences or []
            for i, p in enumerate(prefs):
                if p == str(branch_id):
                    pref_order = i + 1
                    break

            candidates.append({
                "rank": idx + 1,
                "application_id": str(app.id),
                "application_number": app.application_number,
                "student_name": student.user.full_name if student.user else None,
                "merit_score": float(app.fee_amount) if app.fee_amount else 0,
                "category": category,
                "branch_preference_order": pref_order,
                "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            })

        return Response({
            "branch_id": branch_id,
            "quota": quota,
            "available_seats": available,
            "candidates": candidates[:limit],
        }, status=status.HTTP_200_OK)


class OfficerAutoAllocateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.role in [User.Role.ADMIN, User.Role.OFFICER]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        branch_id = request.data.get("branch_id")
        quota = request.data.get("quota")
        count = int(request.data.get("count", 0))

        if not branch_id or not quota:
            return Response(
                {"error": "branch_id, quota, and count are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if count < 1 or count > 50:
            return Response(
                {"error": "count must be between 1 and 50"},
                status=status.HTTP_400_BAD_REQUEST
            )

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return Response(
                {"error": "No current academic year"},
                status=status.HTTP_400_BAD_REQUEST
            )

        seat_row = SeatMatrix.objects.select_for_update().filter(
            academic_year=current_year,
            branch_id=branch_id,
            quota=quota,
        ).first()

        if not seat_row or seat_row.allocated_seats + count > seat_row.total_seats:
            return Response(
                {"error": f"Insufficient seats. Available: {seat_row.total_seats - seat_row.allocated_seats if seat_row else 0}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        applications = Application.objects.select_for_update().filter(
            status__in=[ApplicationStatus.VERIFIED, ApplicationStatus.UNDER_VERIFICATION],
            allocated_branch__isnull=True,
        ).filter(
            branch_preferences__contains=[str(branch_id)]
        ).order_by("-fee_amount", "submitted_at")

        results = []
        allocated = 0

        try:
            with transaction.atomic():
                for app in applications:
                    if allocated >= count:
                        break

                    student = app.student
                    category = getattr(student, "category", None)
                    if not _is_eligible_for_quota(category, quota):
                        continue

                    try:
                        allocate_seat(app.id, branch_id, quota, actor=request.user)
                        results.append({
                            "application_id": str(app.id),
                            "application_number": app.application_number,
                            "success": True,
                        })
                        allocated += 1
                    except SeatUnavailableError as e:
                        results.append({
                            "application_id": str(app.id),
                            "application_number": app.application_number,
                            "success": False,
                            "error": str(e),
                        })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        seat_row.refresh_from_db()
        return Response({
            "requested": count,
            "allocated": allocated,
            "remaining_seats": seat_row.total_seats - seat_row.allocated_seats,
            "results": results,
        }, status=status.HTTP_200_OK)