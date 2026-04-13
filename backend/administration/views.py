from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache
from django.db import transaction
from django.db.models import Sum, Count, Q, Avg, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from verification.models import AuditLog
from verification.serializers import AuditLogSerializer
from agents.pagination import StandardPagination
from admissions.models import Application
from .models import AcademicYear, Branch, QuotaType, SeatMatrix
from .services.ocr_health import get_ocr_stats
from .serializers import SeatMatrixSerializer, SeatMatrixBulkUpsertSerializer


class OCRHealthView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not (request.user.is_superuser or request.user.role == User.Role.ADMIN):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        return Response(get_ocr_stats(), status=status.HTTP_200_OK)


class BranchListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return Response([], status=status.HTTP_200_OK)

        active_branches = Branch.objects.filter(is_active=True).order_by("name")
        seat_rows = SeatMatrix.objects.filter(
            academic_year=current_year,
            branch__in=active_branches,
        )

        seat_index = {
            (str(seat.branch_id), seat.quota): seat
            for seat in seat_rows
        }

        payload = []
        for branch in active_branches:
            available_seats = {}
            total_available = 0

            for quota, _label in QuotaType.choices:
                cache_key = f"seats:{branch.id}:{quota}"
                cached = cache.get(cache_key)
                if cached is None:
                    seat = seat_index.get((str(branch.id), quota))
                    total = int(seat.total_seats) if seat else 0
                    allocated = int(seat.allocated_seats) if seat else 0
                    available = max(total - allocated, 0)
                    cached = {"total": total, "available": available}
                    cache.set(cache_key, cached, timeout=10)

                available_seats[quota] = cached
                total_available += int(cached["available"])

            payload.append(
                {
                    "id": str(branch.id),
                    "name": branch.name,
                    "code": branch.code,
                    "available_seats": available_seats,
                    "total_available": total_available,
                }
            )

        return Response(payload, status=status.HTTP_200_OK)


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class SeatMatrixListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.role in [User.Role.ADMIN, User.Role.PRINCIPAL]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return Response(
                {"error": "No current academic year found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        seat_matrices = SeatMatrix.objects.filter(
            academic_year=current_year,
        ).select_related("branch").order_by("branch__name", "quota")

        data = []
        for sm in seat_matrices:
            data.append({
                "id": str(sm.id),
                "branch_id": str(sm.branch.id),
                "branch_name": sm.branch.name,
                "branch_code": sm.branch.code,
                "quota": sm.quota,
                "quota_label": sm.get_quota_display(),
                "total_seats": sm.total_seats,
                "allocated_seats": sm.allocated_seats,
                "available": max(sm.total_seats - sm.allocated_seats, 0),
                "created_at": sm.created_at.isoformat(),
                "updated_at": sm.updated_at.isoformat(),
            })

        branch_totals = SeatMatrix.objects.filter(
            academic_year=current_year,
        ).values("branch__id", "branch__name", "branch__code").annotate(
            total_seats_sum=Sum("total_seats"),
            allocated_seats_sum=Sum("allocated_seats"),
        )

        summary = {
            "academic_year": current_year.year_label,
            "branches": data,
            "branch_totals": [
                {
                    "branch_id": str(bt["branch__id"]),
                    "branch_name": bt["branch__name"],
                    "branch_code": bt["branch__code"],
                    "total_seats": bt["total_seats_sum"] or 0,
                    "allocated_seats": bt["allocated_seats_sum"] or 0,
                    "available": max((bt["total_seats_sum"] or 0) - (bt["allocated_seats_sum"] or 0), 0),
                }
                for bt in branch_totals
            ],
            "grand_total": {
                "total_seats": sum(sm.total_seats for sm in seat_matrices),
                "allocated_seats": sum(sm.allocated_seats for sm in seat_matrices),
                "available": sum(max(sm.total_seats - sm.allocated_seats, 0) for sm in seat_matrices),
            },
        }

        return Response(summary, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.role in [User.Role.ADMIN, User.Role.PRINCIPAL]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        serializer = SeatMatrixBulkUpsertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return Response(
                {"error": "No current academic year found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        items = serializer.validated_data["items"]
        branch_ids = {item["branch"].id for item in items}
        quotas = {item["quota"] for item in items}

        existing = SeatMatrix.objects.filter(
            academic_year=current_year,
            branch_id__in=branch_ids,
            quota__in=quotas,
        )
        existing_index = {
            (str(sm.branch_id), sm.quota): sm
            for sm in existing
        }

        audit_logs = []
        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for item in items:
                key = (str(item["branch"].id), item["quota"])
                existing_sm = existing_index.get(key)

                if existing_sm:
                    before = {
                        "total_seats": existing_sm.total_seats,
                        "allocated_seats": existing_sm.allocated_seats,
                    }
                    existing_sm.total_seats = item["total_seats"]
                    existing_sm.save(update_fields=["total_seats", "updated_at"])

                    after = {
                        "total_seats": existing_sm.total_seats,
                        "allocated_seats": existing_sm.allocated_seats,
                    }

                    if before != after:
                        audit_logs.append(AuditLog(
                            entity_type="seat_matrix",
                            entity_id=existing_sm.id,
                            action="update",
                            user=request.user,
                            before_json=before,
                            after_json=after,
                            ip_address=get_client_ip(request),
                        ))
                        updated_count += 1
                else:
                    new_sm = SeatMatrix(
                        branch=item["branch"],
                        academic_year=current_year,
                        quota=item["quota"],
                        total_seats=item["total_seats"],
                        allocated_seats=0,
                    )
                    new_sm.save()

                    before = None
                    after = {
                        "total_seats": new_sm.total_seats,
                        "allocated_seats": 0,
                    }

                    audit_logs.append(AuditLog(
                        entity_type="seat_matrix",
                        entity_id=new_sm.id,
                        action="create",
                        user=request.user,
                        before_json=before,
                        after_json=after,
                        ip_address=get_client_ip(request),
                    ))
                    created_count += 1

            if audit_logs:
                AuditLog.objects.bulk_create(audit_logs)

        cache.delete_pattern("seats:*")

        return Response({
            "message": f"Seat matrix updated",
            "created": created_count,
            "updated": updated_count,
        }, status=status.HTTP_200_OK)


class SeatMatrixDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        if not request.user.role in [User.Role.ADMIN, User.Role.PRINCIPAL]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            sm = SeatMatrix.objects.get(pk=pk)
        except SeatMatrix.DoesNotExist:
            return Response(
                {"error": "Seat matrix not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        total_seats = request.data.get("total_seats")
        if total_seats is None:
            return Response(
                {"error": "total_seats is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            total_seats = int(total_seats)
            if total_seats < 0:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {"error": "total_seats must be a non-negative integer"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if total_seats < sm.allocated_seats:
            return Response(
                {"error": f"Cannot reduce below allocated seats ({sm.allocated_seats})"},
                status=status.HTTP_400_BAD_REQUEST
            )

        before = {
            "total_seats": sm.total_seats,
            "allocated_seats": sm.allocated_seats,
        }
        sm.total_seats = total_seats
        sm.save(update_fields=["total_seats", "updated_at"])

        after = {
            "total_seats": sm.total_seats,
            "allocated_seats": sm.allocated_seats,
        }

        AuditLog.objects.create(
            entity_type="seat_matrix",
            entity_id=sm.id,
            action="update",
            user=request.user,
            before_json=before,
            after_json=after,
            ip_address=get_client_ip(request),
        )

        cache.delete_pattern("seats:*")

        serializer = SeatMatrixSerializer(sm)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        if not request.user.role in [User.Role.ADMIN, User.Role.PRINCIPAL]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            sm = SeatMatrix.objects.get(pk=pk)
        except SeatMatrix.DoesNotExist:
            return Response(
                {"error": "Seat matrix not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        before = {
            "branch": str(sm.branch_id),
            "quota": sm.quota,
            "total_seats": sm.total_seats,
            "allocated_seats": sm.allocated_seats,
        }

        AuditLog.objects.create(
            entity_type="seat_matrix",
            entity_id=sm.id,
            action="delete",
            user=request.user,
            before_json=before,
            after_json=None,
            ip_address=get_client_ip(request),
        )

        sm.delete()
        cache.delete_pattern("seats:*")

        return Response(status=status.HTTP_204_NO_CONTENT)


class AdmissionStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.role in [User.Role.ADMIN, User.Role.PRINCIPAL]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        from admissions.models import Application, ApplicationStatus

        current_year = AcademicYear.objects.filter(is_current=True).first()
        apps = Application.objects.filter(
            created_at__gte=current_year.start_date
        ) if current_year else Application.objects.none()

        # Status breakdown
        status_counts = {}
        for status_val, _ in ApplicationStatus.choices:
            status_counts[status_val] = apps.filter(status=status_val).count()

        total = apps.count()
        today = timezone.now().date()
        today_count = apps.filter(created_at__date=today).count()
        this_week = apps.filter(created_at__gte=timezone.now() - timedelta(days=7)).count()

        # Conversion funnel
        submitted = apps.exclude(status=ApplicationStatus.DRAFT).count()
        verified = apps.filter(
            status__in=[
                ApplicationStatus.VERIFIED,
                ApplicationStatus.SEAT_ALLOCATED,
                ApplicationStatus.FEE_PENDING,
                ApplicationStatus.ADMITTED,
            ]
        ).count()
        admitted = apps.filter(status=ApplicationStatus.ADMITTED).count()
        rejected = apps.filter(status=ApplicationStatus.REJECTED).count()

        # Avg processing time (days)
        avg_delta = apps.filter(
            admitted_at__isnull=False, submitted_at__isnull=False
        ).aggregate(
            avg=Avg(F('admitted_at') - F('submitted_at'))
        )['avg']
        
        avg_processing_days = round(avg_delta.total_seconds() / 86400, 1) if avg_delta else None

        return Response({
            'academic_year': current_year.year_label if current_year else None,
            'total_applications': total,
            'today': today_count,
            'this_week': this_week,
            'status_breakdown': status_counts,
            'funnel': {
                'submitted': submitted,
                'verified': verified,
                'admitted': admitted,
                'rejected': rejected,
                'conversion_rate': round((admitted / submitted * 100), 1) if submitted else 0,
            },
            'avg_processing_days': avg_processing_days,
        }, status=status.HTTP_200_OK)


class AdmissionTrendView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.ADMIN, User.Role.PRINCIPAL]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        from admissions.models import Application, ApplicationStatus

        period = request.query_params.get("period", "daily")
        if period not in {"daily", "weekly", "monthly"}:
            return Response(
                {"error": "period must be one of: daily, weekly, monthly"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        days_raw = request.query_params.get("days", 30)
        try:
            days = int(days_raw)
            if days <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "days must be a positive integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        since = timezone.now() - timedelta(days=days)
        trunc_fn = {
            "daily": TruncDate,
            "weekly": TruncWeek,
            "monthly": TruncMonth,
        }[period]

        submitted_trend = (
            Application.objects.filter(submitted_at__gte=since, submitted_at__isnull=False)
            .annotate(period=trunc_fn("submitted_at"))
            .values("period")
            .annotate(count=Count("id"))
            .order_by("period")
        )

        admitted_trend = (
            Application.objects.filter(admitted_at__gte=since, admitted_at__isnull=False)
            .annotate(period=trunc_fn("admitted_at"))
            .values("period")
            .annotate(count=Count("id"))
            .order_by("period")
        )

        rejected_trend = (
            Application.objects.filter(
                status=ApplicationStatus.REJECTED,
                updated_at__gte=since,
            )
            .annotate(period=trunc_fn("updated_at"))
            .values("period")
            .annotate(count=Count("id"))
            .order_by("period")
        )

        return Response(
            {
                "period": period,
                "submitted": [{"date": e["period"].isoformat(), "count": e["count"]} for e in submitted_trend],
                "admitted": [{"date": e["period"].isoformat(), "count": e["count"]} for e in admitted_trend],
                "rejected": [{"date": e["period"].isoformat(), "count": e["count"]} for e in rejected_trend],
            },
            status=status.HTTP_200_OK,
        )


class SeatFillStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.ADMIN, User.Role.PRINCIPAL]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return Response({"error": "No current academic year"}, status=status.HTTP_400_BAD_REQUEST)

        seat_rows = SeatMatrix.objects.filter(academic_year=current_year)
        totals = seat_rows.aggregate(
            total_seats=Sum("total_seats"),
            allocated_seats=Sum("allocated_seats"),
        )

        total = totals["total_seats"] or 0
        allocated = totals["allocated_seats"] or 0
        available = max(total - allocated, 0)
        fill_percentage = round((allocated / total * 100), 1) if total else 0

        by_branch = (
            seat_rows.values("branch__id", "branch__name", "branch__code")
            .annotate(total_seats=Sum("total_seats"), allocated_seats=Sum("allocated_seats"))
            .order_by("branch__name")
        )

        return Response(
            {
                "total_seats": total,
                "allocated_seats": allocated,
                "available_seats": available,
                "fill_percentage": fill_percentage,
                "by_branch": [
                    {
                        "branch_id": str(item["branch__id"]),
                        "branch_name": item["branch__name"],
                        "branch_code": item["branch__code"],
                        "total_seats": item["total_seats"] or 0,
                        "allocated_seats": item["allocated_seats"] or 0,
                        "available_seats": max((item["total_seats"] or 0) - (item["allocated_seats"] or 0), 0),
                    }
                    for item in by_branch
                ],
            },
            status=status.HTTP_200_OK,
        )


class AgentPerformanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.ADMIN, User.Role.PRINCIPAL]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        from agents.models import AgentProfile, CommissionRecord, CommissionStatus
        from admissions.models import ApplicationStatus

        agent_rows = (
            AgentProfile.objects.select_related("user")
            .annotate(
                total_students=Count("students", distinct=True),
                admitted_students=Count(
                    "students__application",
                    filter=Q(students__application__status=ApplicationStatus.ADMITTED),
                    distinct=True,
                ),
            )
            .order_by("-admitted_students", "-total_students", "agency_name")
        )

        agents_data = []
        total_referred = 0
        total_admitted = 0
        total_commission = 0

        for agent in agent_rows:
            # Count students by status
            student_apps = agent.students.all().select_related('application')

            referred = agent.total_students
            admitted = agent.admitted_students

            status_counts = {
                'pending': 0,
                'rejected': 0,
            }

            for student in student_apps:
                if student.application:
                    if student.application.status == ApplicationStatus.REJECTED:
                        status_counts['rejected'] += 1
                    elif student.application.status not in [ApplicationStatus.ADMITTED, ApplicationStatus.SUBMITTED]:
                        status_counts['pending'] += 1

            # Calculate conversion rate
            conversion_rate = (admitted / referred * 100) if referred > 0 else 0

            # Get commission data
            commissions = CommissionRecord.objects.filter(agent=agent)
            commission_stats = commissions.aggregate(
                paid=Sum('commission_amount', filter=Q(status=CommissionStatus.PAID)),
                pending=Sum('commission_amount', filter=Q(status__in=[CommissionStatus.PENDING, CommissionStatus.APPROVED]))
            )

            commission_paid = float(commission_stats['paid'] or 0)
            commission_pending = float(commission_stats['pending'] or 0)

            total_referred += referred
            total_admitted += admitted
            total_commission += commission_paid

            agents_data.append({
                "agent_id": str(agent.id),
                "name": agent.agency_name or (agent.user.full_name if agent.user else ""),
                "email": agent.user.email if agent.user else None,
                "is_verified": agent.is_verified,
                "referred": referred,
                "admitted": admitted,
                "pending": status_counts['pending'],
                "rejected": status_counts['rejected'],
                "conversion_rate": round(conversion_rate, 1),
                "commission_paid": str(commission_paid),
                "commission_pending": str(commission_pending),
            })

        return Response(
            {
                "summary": {
                    "total_agents": agent_rows.count(),
                    "total_referred": total_referred,
                    "total_admitted_via_agents": total_admitted,
                    "total_commission_paid": str(total_commission),
                },
                "agents": agents_data,
            },
            status=status.HTTP_200_OK,
        )


class RevenueStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.role in [User.Role.ADMIN, User.Role.PRINCIPAL]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        from admissions.models import Application, ApplicationStatus
        from agents.models import CommissionRecord

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return Response({'error': 'No current academic year'}, status=status.HTTP_400_BAD_REQUEST)

        apps = Application.objects.filter(
            created_at__gte=current_year.start_date
        )

        collected = apps.filter(fee_paid=True).aggregate(
            total=Sum(F('fee_amount') - F('fee_concession')),
            count=Count('id'),
        )
        pending = apps.filter(
            status=ApplicationStatus.FEE_PENDING, fee_paid=False
        ).aggregate(
            total=Sum(F('fee_amount') - F('fee_concession')),
            count=Count('id'),
        )
        concessions = apps.filter(fee_paid=True).aggregate(
            total=Sum('fee_concession'),
        )

        # Commission liability
        commission_data = CommissionRecord.objects.filter(
            application__student__user__date_joined__gte=current_year.start_date
        ).aggregate(
            total_pending=Sum('commission_amount', filter=Q(status='pending')),
            total_approved=Sum('commission_amount', filter=Q(status='approved')),
            total_paid=Sum('commission_amount', filter=Q(status='paid')),
        )

        # Daily collection trend (last 30 days)
        daily_trend = (
            apps.filter(fee_paid=True, fee_paid_at__gte=timezone.now() - timedelta(days=30))
            .annotate(date=TruncDate('fee_paid_at'))
            .values('date')
            .annotate(
                amount=Sum(F('fee_amount') - F('fee_concession')),
                count=Count('id'),
            )
            .order_by('date')
        )

        return Response({
            'collected': {
                'amount': str(collected['total'] or 0),
                'count': collected['count'] or 0,
            },
            'pending': {
                'amount': str(pending['total'] or 0),
                'count': pending['count'] or 0,
            },
            'concessions_given': str(concessions['total'] or 0),
            'commissions': {
                'pending': str(commission_data['total_pending'] or 0),
                'approved': str(commission_data['total_approved'] or 0),
                'paid': str(commission_data['total_paid'] or 0),
            },
            'net_revenue': str(
                (collected['total'] or 0) - (commission_data['total_paid'] or 0)
            ),
            'daily_trend': [
                {
                    'date': entry['date'].isoformat(),
                    'amount': str(entry['amount']),
                    'count': entry['count'],
                }
                for entry in daily_trend
            ],
        }, status=status.HTTP_200_OK)


class VerificationPerformanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.role in [User.Role.ADMIN, User.Role.PRINCIPAL]:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        from accounts.models import User
        from verification.models import AuditLog
        from admissions.models import Application, ApplicationStatus

        staff = User.objects.filter(role=User.Role.VERIFICATION_STAFF, is_active=True)
        now = timezone.now()
        last_7_days = now - timedelta(days=7)

        staff_metrics = []
        for member in staff:
            claimed_count = Application.objects.filter(claimed_by=member).count()
            active_claims = Application.objects.filter(
                claimed_by=member,
                status=ApplicationStatus.UNDER_VERIFICATION,
            ).count()
            
            # Application-level locks performed by this staff
            verified_total = AuditLog.objects.filter(
                user=member, entity_type='application', action='LOCK'
            ).count()
            
            verified_recent = AuditLog.objects.filter(
                user=member, 
                entity_type='application', 
                action='LOCK',
                timestamp__gte=last_7_days
            ).count()

            # Calculate turnaround time
            recent_lock_logs = AuditLog.objects.filter(
                user=member, 
                entity_type='application', 
                action='LOCK',
                timestamp__gte=last_7_days
            ).values_list('entity_id', flat=True)

            avg_turnaround = None
            if recent_lock_logs:
                avg_delta = Application.objects.filter(
                    id__in=recent_lock_logs,
                    claimed_at__isnull=False,
                    locked_at__isnull=False
                ).aggregate(
                    avg=Avg(ExpressionWrapper(F('locked_at') - F('claimed_at'), output_field=DurationField()))
                )['avg']
                
                if avg_delta:
                    avg_turnaround = round(avg_delta.total_seconds() / 3600, 1) # Hours

            staff_metrics.append({
                'user_id': str(member.id),
                'name': member.full_name,
                'email': member.email,
                'active_claims': active_claims,
                'total_claimed': claimed_count,
                'verified_total': verified_total,
                'verified_this_week': verified_recent,
                'avg_turnaround_hours': avg_turnaround,
            })

        # Queue health
        pending_queue = Application.objects.filter(
            status__in=[ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_VERIFICATION]
        ).count()
        
        unclaimed = Application.objects.filter(
            status=ApplicationStatus.SUBMITTED,
            claimed_by__isnull=True,
        ).count()
        
        oldest_unclaimed_app = Application.objects.filter(
            status=ApplicationStatus.SUBMITTED,
            claimed_by__isnull=True,
        ).order_by('submitted_at').first()

        oldest_submitted_at = oldest_unclaimed_app.submitted_at if oldest_unclaimed_app else None

        return Response({
            'staff': sorted(staff_metrics, key=lambda s: s['verified_this_week'], reverse=True),
            'queue_health': {
                'total_pending_verification': pending_queue,
                'unclaimed_in_queue': unclaimed,
                'oldest_unclaimed_at': oldest_submitted_at.isoformat() if oldest_submitted_at else None,
                'oldest_age_hours': round(
                    (now - oldest_submitted_at).total_seconds() / 3600, 1
                ) if oldest_submitted_at else 0,
            },
        }, status=status.HTTP_200_OK)


class AuditTrailView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role not in (User.Role.PRINCIPAL, User.Role.ADMIN):
            return AuditLog.objects.none()

        qs = AuditLog.objects.select_related('user', 'application').all()

        # Filters
        app_id = self.request.query_params.get('application')
        if app_id:
            qs = qs.filter(application_id=app_id)

        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)

        action = self.request.query_params.get('action')
        if action:
            qs = qs.filter(action=action)

        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(application__application_number__icontains=search) |
                Q(user__full_name__icontains=search) |
                Q(field_name__icontains=search)
            )

        return qs.order_by('-timestamp')
