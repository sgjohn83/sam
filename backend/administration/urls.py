from django.urls import path

from .views import (
    OCRHealthView, BranchListView, SeatMatrixListView, SeatMatrixDetailView, 
    AdmissionStatsView, AdmissionTrendView, SeatFillStatsView, RevenueStatsView, 
    AgentPerformanceView, VerificationPerformanceView, AuditTrailView
)
from agents.views import (
    CommissionApproveView, CommissionRejectView, 
    CommissionMarkPaidView, AdminCommissionListView,
    BulkPayCommissionsView, AdminAgentListView
)

urlpatterns = [
    path("ocr-health/", OCRHealthView.as_view(), name="admin-ocr-health"),
    path("branches/", BranchListView.as_view(), name="admin-branches"),
    path("agents/", AdminAgentListView.as_view(), name="admin-agents"),
    path("seat-matrix/", SeatMatrixListView.as_view(), name="admin-seat-matrix"),
    path("seat-matrix/<uuid:pk>/", SeatMatrixDetailView.as_view(), name="admin-seat-matrix-detail"),
    path("stats/admissions/", AdmissionStatsView.as_view(), name="principal-admission-stats"),
    path("stats/trend/", AdmissionTrendView.as_view(), name="principal-admission-trend"),
    path("stats/seats/", SeatFillStatsView.as_view(), name="principal-seat-stats"),
    path("stats/revenue/", RevenueStatsView.as_view(), name="principal-revenue-stats"),
    path("stats/agents/", AgentPerformanceView.as_view(), name="principal-agent-stats"),
    path("stats/verification/", VerificationPerformanceView.as_view(), name="principal-verification-stats"),
    path("audit-trail/", AuditTrailView.as_view(), name="admin-audit-trail"),
]
