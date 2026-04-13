"""
Principal-scoped audit trail and compliance views.

These endpoints give the principal full read-only access to ALL audit
entries across the system — not scoped to a single application like
the per-application audit log in the verification views.
"""

import csv
from django.db.models import Q
from django.http import StreamingHttpResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from .models import AuditLog
from .serializers import AuditLogSerializer


class IsPrincipalOrAdmin(permissions.BasePermission):
    """Allows access only to principal or admin roles."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in (User.Role.PRINCIPAL, User.Role.ADMIN)


class AuditTrailView(generics.ListAPIView):
    """
    GET /api/principal/audit-trail/

    Full audit log viewer for compliance review. Supports filters:
      - application  : UUID — filter by entity_id where entity_type=application,
                       or by any entity linked to that application
      - user         : UUID — filter by actor
      - action       : string — exact match (field_edit, claim, release, etc.)
      - entity_type  : string — exact match (application, document, ocr_result, commission)
      - date_from    : YYYY-MM-DD
      - date_to      : YYYY-MM-DD
      - search       : free text — searches actor name and entity_type
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsPrincipalOrAdmin]

    def get_queryset(self):
        qs = AuditLog.objects.select_related('user').all()

        # --- Filters ---

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
            from django.db.models import Q
            qs = qs.filter(
                Q(user__full_name__icontains=search)
                | Q(user__email__icontains=search)
                | Q(entity_type__icontains=search)
                | Q(action__icontains=search)
            )

        return qs.order_by('-timestamp')


class AuditTrailActionsView(APIView):
    """
    GET /api/principal/audit-trail/actions/

    Returns the distinct action values and entity types present in the audit log,
    plus the list of active audit-relevant users, so the frontend can populate
    filter dropdowns dynamically.
    """

    permission_classes = [IsPrincipalOrAdmin]

    def get(self, request):
        actions = (
            AuditLog.objects
            .values_list('action', flat=True)
            .distinct()
            .order_by('action')
        )
        entity_types = (
            AuditLog.objects
            .values_list('entity_type', flat=True)
            .distinct()
            .order_by('entity_type')
        )

        # Get users who have actually performed audited actions
        users_with_actions = (
            User.objects
            .filter(
                audit_actions__isnull=False,
                is_active=True,
            )
            .distinct()
            .values('id', 'full_name', 'email', 'role')
            .order_by('full_name')
        )

        return Response({
            'actions': list(actions),
            'entity_types': list(entity_types),
            'users': [
                {
                    'id': str(u['id']),
                    'name': u['full_name'],
                    'email': u['email'],
                    'role': u['role'],
                }
                for u in users_with_actions
            ],
        })


class AuditTrailExportView(APIView):
    """
    GET /api/principal/audit-trail/export/?date_from=&date_to=&action=&user=

    Streams a CSV download of filtered audit entries for compliance reporting.
    Uses iterator with chunk_size to handle large datasets without memory issues.
    """

    permission_classes = [IsPrincipalOrAdmin]

    def get(self, request):
        qs = AuditLog.objects.select_related('user').all()

        # Apply same filters as the list view
        app_id = request.query_params.get('application')
        if app_id:
            qs = qs.filter(application_id=app_id)

        user_id = request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)

        action = request.query_params.get('action')
        if action:
            qs = qs.filter(action=action)

        entity_type = request.query_params.get('entity_type')
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        date_from = request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)

        date_to = request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)

        qs = qs.order_by('-timestamp')

        response = StreamingHttpResponse(
            self._generate_csv(qs),
            content_type='text/csv',
        )

        filename = f'audit_trail_{date_from or "all"}_to_{date_to or "all"}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @staticmethod
    def _generate_csv(queryset):
        """Yield CSV rows using an iterator so large logs don't fill memory."""
        # Use Python's csv module for proper escaping (handles commas,
        # quotes, newlines in JSON fields).
        import io
        import json

        header = [
            'Timestamp', 'User Name', 'User Email', 'User Role',
            'Application Number', 'Action', 'Entity Type', 'Entity ID',
            'Field Name', 'Old Value', 'New Value', 'Before JSON', 'After JSON',
            'IP Address', 'User Agent',
        ]
        # Yield header
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(header)
        yield buf.getvalue()

        # Yield data rows in chunks
        for log in queryset.select_related('user', 'application').iterator(chunk_size=500):
            buf = io.StringIO()
            writer = csv.writer(buf)

            before_str = json.dumps(log.before_json) if log.before_json else ''
            after_str = json.dumps(log.after_json) if log.after_json else ''

            writer.writerow([
                log.timestamp.isoformat(),
                log.user.full_name if log.user else '',
                log.user.email if log.user else '',
                log.user.role if log.user else '',
                log.application.application_number if log.application else '',
                log.action,
                log.entity_type,
                str(log.entity_id),
                log.field_name or '',
                log.old_value or '',
                log.new_value or '',
                before_str,
                after_str,
                str(log.ip_address) if log.ip_address else '',
                log.user_agent or '',
            ])
            yield buf.getvalue()
