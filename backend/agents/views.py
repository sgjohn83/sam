import uuid
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction, connection
from django.db.models import Sum, Count, Q
from django.core.exceptions import PermissionDenied

from accounts.models import User
from admissions.models import Application, ApplicationStatus
from students.models import StudentProfile, StudentCategory
from verification.models import AuditLog
from notifications.tasks import send_notification
from administration.views import get_client_ip
from documents.models import Document

from .models import AgentProfile, CommissionRecord, CommissionStatus
from .serializers import (
    AgentProfileSerializer, AgentStudentSerializer, 
    CommissionRecordSerializer, AgentRegisterStudentSerializer,
    AgentStudentDetailSerializer
)
from .pagination import StandardPagination


class IsAgent(BasePermission):
    def has_permission(self, request, view):
        if not (request.user.is_authenticated and request.user.role == 'agent'):
            return False
        
        try:
            return request.user.agent_profile.is_active
        except AgentProfile.DoesNotExist:
            return False


class AgentDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAgent]

    def get(self, request):
        agent = request.user.agent_profile
        
        # Student stats
        students = StudentProfile.objects.filter(agent=agent)
        total_students = students.count()
        admitted_students = students.filter(application__status=ApplicationStatus.ADMITTED).count()
        
        # Commission stats
        commissions = CommissionRecord.objects.filter(agent=agent)
        stats = commissions.aggregate(
            pending_amount=Sum('commission_amount', filter=Q(status=CommissionStatus.PENDING)),
            paid_amount=Sum('commission_amount', filter=Q(status=CommissionStatus.PAID)),
            lifetime_earned=Sum('commission_amount', filter=Q(status__in=[CommissionStatus.PAID, CommissionStatus.APPROVED]))
        )

        # Recent activities
        recent_students = students.order_by('-created_at')[:5]
        recent_commissions = commissions.order_by('-created_at')[:5]

        return Response({
            'agent': AgentProfileSerializer(agent).data,
            'students': {
                'total_referred': total_students,
                'admitted': admitted_students,
            },
            'commission': {
                'pending_amount': str(stats['pending_amount'] or 0),
                'paid_amount': str(stats['paid_amount'] or 0),
                'lifetime_earned': str(stats['lifetime_earned'] or 0),
            },
            'recent_students': AgentStudentSerializer(recent_students, many=True).data,
            'recent_commissions': CommissionRecordSerializer(recent_commissions, many=True).data,
        })


class AgentStudentListView(generics.ListAPIView):
    serializer_class = AgentStudentSerializer
    permission_classes = [IsAuthenticated, IsAgent]
    pagination_class = StandardPagination

    def get_queryset(self):
        try:
            agent = self.request.user.agent_profile
        except AgentProfile.DoesNotExist:
            return StudentProfile.objects.none()

        qs = StudentProfile.objects.filter(
            agent=agent
        ).select_related('user', 'application', 'application__allocated_branch')

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(application__status=status_param)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(user__full_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(application__application_number__icontains=search)
            )

        return qs.order_by('-application__submitted_at')


class AgentStudentDetailView(generics.RetrieveAPIView):
    serializer_class = AgentStudentDetailSerializer
    permission_classes = [IsAuthenticated, IsAgent]

    def get_queryset(self):
        try:
            agent = self.request.user.agent_profile
        except AgentProfile.DoesNotExist:
            return StudentProfile.objects.none()

        return StudentProfile.objects.filter(
            agent=agent
        ).select_related('user', 'application', 'application__allocated_branch')


class AgentCommissionListView(generics.ListAPIView):
    serializer_class = CommissionRecordSerializer
    permission_classes = [IsAuthenticated, IsAgent]
    pagination_class = StandardPagination

    def get_queryset(self):
        try:
            agent = self.request.user.agent_profile
        except AgentProfile.DoesNotExist:
            return CommissionRecord.objects.none()

        qs = CommissionRecord.objects.filter(
            agent=agent
        ).select_related('application', 'student__user', 'application__allocated_branch')

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        return qs.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)

        # Agent-specific summary
        agent = request.user.agent_profile
        stats = CommissionRecord.objects.filter(agent=agent).aggregate(
            total_pending=Sum('commission_amount', filter=Q(status=CommissionStatus.PENDING)),
            total_approved=Sum('commission_amount', filter=Q(status=CommissionStatus.APPROVED)),
            total_paid=Sum('commission_amount', filter=Q(status=CommissionStatus.PAID)),
            count_pending=Count('id', filter=Q(status=CommissionStatus.PENDING)),
        )

        response.data['summary'] = {
            'pending_amount': str(stats['total_pending'] or 0),
            'pending_count': stats['count_pending'] or 0,
            'approved_amount': str(stats['total_approved'] or 0),
            'paid_amount': str(stats['total_paid'] or 0),
            'total_earned': str((stats['total_paid'] or 0) + (stats['total_approved'] or 0)),
        }

        return response


class AgentRegisterStudentView(APIView):
    permission_classes = [IsAuthenticated, IsAgent]

    def post(self, request):
        agent_profile = request.user.agent_profile
        if not agent_profile.is_verified:
            return Response({'error': 'Agent account not yet verified'}, status=403)

        serializer = AgentRegisterStudentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        validated = serializer.validated_data

        # Create user with role=student
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=validated['email'],
                    full_name=validated['full_name'],
                    role='student',
                    password=str(uuid.uuid4())[:12] # temp password
                )
                
                # Create student profile
                student = StudentProfile.objects.create(
                    user=user,
                    agent=agent_profile,
                    mobile_number=validated['phone'],
                    category=validated.get('category', 'general')
                )

                # Send invite notification
                send_notification.delay(
                    notification_type='agent_student_invite',
                    user_id=str(user.id),
                    context={
                        'student_name': user.full_name,
                        'agent_name': agent_profile.agency_name or request.user.full_name,
                        'email': user.email,
                        'support_email': 'support@college.edu'
                    }
                )

                return Response({
                    'message': 'Student registered successfully',
                    'student_id': student.id
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=400)


class CommissionApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role not in ('admin', 'principal'):
            return Response({"error": "Unauthorized"}, status=403)

        commission = get_object_or_404(CommissionRecord, id=pk)
        if commission.status != CommissionStatus.PENDING:
            return Response({'error': f'Cannot approve a {commission.status} commission'}, status=400)

        before = {'status': commission.status}
        commission.status = CommissionStatus.APPROVED
        commission.approved_by = request.user
        commission.approved_at = timezone.now()
        commission.save()
        after = {'status': commission.status}

        AuditLog.objects.create(
            user=request.user,
            application=commission.application,
            entity_type='commission',
            entity_id=commission.id,
            action='commission_approve',
            before_json=before,
            after_json=after,
            ip_address=get_client_ip(request),
        )

        # Notify Agent
        send_notification.delay(
            notification_type='commission_approved',
            user_id=str(commission.agent.user_id),
            context={
                'email': commission.agent.user.email,
                'agent_name': commission.agent.agency_name or commission.agent.user.full_name,
                'commission_amount': str(commission.commission_amount),
                'student_name': commission.student.user.full_name,
            },
        )

        return Response(CommissionRecordSerializer(commission).data)


class CommissionRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role not in ('admin', 'principal'):
            return Response({"error": "Unauthorized"}, status=403)

        notes = request.data.get('notes')
        if not notes:
            return Response({'error': 'Reason for rejection is required in notes field.'}, status=400)

        commission = get_object_or_404(CommissionRecord, id=pk)
        if commission.status != CommissionStatus.PENDING:
            return Response({'error': f'Cannot reject a {commission.status} commission'}, status=400)

        before = {'status': commission.status, 'notes': commission.notes}
        commission.status = CommissionStatus.REJECTED
        commission.notes = notes
        commission.save()
        after = {'status': commission.status, 'notes': commission.notes}

        AuditLog.objects.create(
            user=request.user,
            application=commission.application,
            entity_type='commission',
            entity_id=commission.id,
            action='commission_reject',
            before_json=before,
            after_json=after,
            ip_address=get_client_ip(request),
        )

        # Notify Agent
        send_notification.delay(
            notification_type='commission_rejected',
            user_id=str(commission.agent.user_id),
            context={
                'email': commission.agent.user.email,
                'agent_name': commission.agent.agency_name or commission.agent.user.full_name,
                'student_name': commission.student.user.full_name,
                'reason': commission.notes,
            },
        )

        return Response(CommissionRecordSerializer(commission).data)


class CommissionMarkPaidView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role not in ('admin', 'principal'):
            return Response({"error": "Unauthorized"}, status=403)

        payment_reference = request.data.get('payment_reference')
        if not payment_reference:
            return Response({'error': 'Payment reference is required.'}, status=400)

        commission = get_object_or_404(CommissionRecord, id=pk)
        if commission.status != CommissionStatus.APPROVED:
            return Response({'error': f'Can only pay an approved commission. Current: {commission.status}'}, status=400)

        before = {'status': commission.status, 'payment_reference': commission.payment_reference}
        commission.status = CommissionStatus.PAID
        commission.paid_at = timezone.now()
        commission.payment_reference = payment_reference
        commission.save()
        after = {'status': commission.status, 'payment_reference': commission.payment_reference}

        AuditLog.objects.create(
            user=request.user,
            application=commission.application,
            entity_type='commission',
            entity_id=commission.id,
            action='commission_paid',
            before_json=before,
            after_json=after,
            ip_address=get_client_ip(request),
        )

        # Notify Agent
        send_notification.delay(
            notification_type='commission_paid',
            user_id=str(commission.agent.user_id),
            context={
                'email': commission.agent.user.email,
                'agent_name': commission.agent.agency_name or commission.agent.user.full_name,
                'total_amount': str(commission.commission_amount),
                'payment_reference': commission.payment_reference,
                'paid_at': commission.paid_at.strftime('%Y-%m-%d %H:%M'),
            },
        )

        return Response(CommissionRecordSerializer(commission).data)


class AdminCommissionListView(generics.ListAPIView):
    serializer_class = CommissionRecordSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role not in ('admin', 'principal'):
            return CommissionRecord.objects.none()

        qs = CommissionRecord.objects.all().select_related(
            'application', 'agent', 'student__user', 'application__allocated_branch'
        )

        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)

        agent_id = self.request.query_params.get('agent')
        if agent_id:
            qs = qs.filter(agent_id=agent_id)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)

        # Admin Summary
        stats = queryset.aggregate(
            pending_amt=Sum('commission_amount', filter=Q(status=CommissionStatus.PENDING)),
            approved_amt=Sum('commission_amount', filter=Q(status=CommissionStatus.APPROVED)),
            paid_amt=Sum('commission_amount', filter=Q(status=CommissionStatus.PAID)),
            pending_count=Count('id', filter=Q(status=CommissionStatus.PENDING)),
            approved_count=Count('id', filter=Q(status=CommissionStatus.APPROVED)),
        )

        response.data['summary'] = {
            'pending_amount': str(stats['pending_amt'] or 0),
            'pending_count': stats['pending_count'] or 0,
            'approved_amount': str(stats['approved_amt'] or 0),
            'approved_count': stats['approved_count'] or 0,
            'paid_amount_this_range': str(stats['paid_amt'] or 0),
        }

        return response


class BulkPayCommissionsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role not in ('admin', 'principal'):
            return Response({"error": "Unauthorized"}, status=403)

        ids = request.data.get('commission_ids', [])
        payment_ref = request.data.get('payment_reference')

        if not payment_ref:
            return Response({'error': 'Payment reference required'}, status=400)

        with transaction.atomic():
            commissions = CommissionRecord.objects.select_for_update().filter(
                id__in=ids, status=CommissionStatus.APPROVED
            )

            if commissions.count() != len(ids):
                return Response({'error': 'Some commissions are not in approved status or not found'}, status=400)

            now = timezone.now()
            
            # Group by agent to send aggregated notifications
            agent_totals = {}
            for comm in commissions:
                agent_id = comm.agent_id
                if agent_id not in agent_totals:
                    agent_totals[agent_id] = {'agent': comm.agent, 'total': 0}
                agent_totals[agent_id]['total'] += comm.commission_amount

            # Update all to paid
            commissions.update(
                status=CommissionStatus.PAID,
                paid_at=now,
                payment_reference=payment_ref
            )

            # Record in AuditLog and trigger notifications
            for agent_id, data in agent_totals.items():
                agent = data['agent']
                batch_amount = data['total']

                # Notify agent
                send_notification.delay(
                    notification_type='commission_paid',
                    user_id=str(agent.user_id),
                    context={
                        'email': agent.user.email,
                        'agent_name': agent.agency_name or agent.user.full_name,
                        'total_amount': str(batch_amount),
                        'payment_reference': payment_ref,
                        'paid_at': now.strftime('%Y-%m-%d %H:%M'),
                    },
                )

                # Log for Admin
                AuditLog.objects.create(
                    user=request.user,
                    entity_type='agent',
                    entity_id=agent.id,
                    action='agent_bulk_payment',
                    before_json={'batch_size': len(ids)},
                    after_json={'payment_reference': payment_ref, 'batch_amount': str(batch_amount)},
                    ip_address=get_client_ip(request),
                )

        return Response({
            'message': f'Successfully processed {len(ids)} commissions',
            'paid_count': len(ids),
            'payment_reference': payment_ref
        })


class AgentProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = AgentProfileSerializer
    permission_classes = [IsAuthenticated, IsAgent]

    def get_object(self):
        return self.request.user.agent_profile


class AdminAgentListView(generics.ListAPIView):
    serializer_class = AgentProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role not in ('admin', 'principal'):
            return AgentProfile.objects.none()
        return AgentProfile.objects.all().order_by('agency_name')


class AgentProfileCompletionView(APIView):
    permission_classes = [IsAuthenticated, IsAgent]

    def get(self, request):
        try:
            agent = request.user.agent_profile
        except AgentProfile.DoesNotExist:
            return Response({"error": "Agent profile not found."}, status=404)

        steps = {
            'basic_info': {
                'complete': bool(agent.agency_name and agent.contact_phone),
                'fields': ['agency_name', 'contact_phone'],
            },
            'bank_details': {
                'complete': bool(agent.bank_account_name and agent.bank_account_number and agent.bank_ifsc),
                'fields': ['bank_account_name', 'bank_account_number', 'bank_ifsc'],
            },
            'pan_verification': {
                'complete': bool(agent.pan_number),
                'fields': ['pan_number'],
            },
            'admin_verification': {
                'complete': agent.is_verified,
                'fields': [],
                'note': 'Pending admin review' if not agent.is_verified else 'Verified',
            },
        }

        completed = sum(1 for s in steps.values() if s['complete'])
        total = len(steps)

        return Response({
            'steps': steps,
            'completed': completed,
            'total': total,
            'percentage': int((completed / total) * 100),
            'can_register_students': agent.is_verified,
            'can_receive_commissions': steps['bank_details']['complete'] and agent.is_verified,
        })


class AgentPipelineSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAgent]

    def get(self, request):
        try:
            agent = request.user.agent_profile
        except AgentProfile.DoesNotExist:
            return Response({"error": "Agent profile not found."}, status=404)

        pipeline = (
            Application.objects
            .filter(student__agent=agent)
            .values('status')
            .annotate(count=Count('id'))
        )
        status_map = {choice[0]: 0 for choice in ApplicationStatus.choices}
        for entry in pipeline:
            status_map[entry['status']] = entry['count']

        return Response({
            'pipeline': status_map,
            'total': sum(status_map.values()),
        })


class AgentCommissionSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAgent]

    def get(self, request):
        from django.db.models.functions import TruncMonth

        try:
            agent = request.user.agent_profile
        except AgentProfile.DoesNotExist:
            return Response({"error": "Agent profile not found."}, status=404)

        monthly = (
            CommissionRecord.objects
            .filter(agent=agent, status=CommissionStatus.PAID)
            .annotate(month=TruncMonth('paid_at'))
            .values('month')
            .annotate(
                total=Sum('commission_amount'),
                count=Count('id'),
            )
            .order_by('-month')[:12]
        )

        return Response({
            'monthly_earnings': [
                {
                    'month': entry['month'].strftime('%Y-%m'),
                    'month_label': entry['month'].strftime('%b %Y'),
                    'total': str(entry['total']),
                    'count': entry['count'],
                }
                for entry in monthly if entry['month']
            ],
            'lifetime': {
                'total_earned': str(agent.total_commission_earned),
                'total_students': agent.total_students_referred,
            },
        })
