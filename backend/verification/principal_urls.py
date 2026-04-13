from django.urls import path
from .principal_views import AuditTrailView, AuditTrailActionsView, AuditTrailExportView

urlpatterns = [
    path('audit-trail/', AuditTrailView.as_view(), name='principal-audit-trail'),
    path('audit-trail/actions/', AuditTrailActionsView.as_view(), name='principal-audit-trail-actions'),
    path('audit-trail/export/', AuditTrailExportView.as_view(), name='principal-audit-trail-export'),
]
