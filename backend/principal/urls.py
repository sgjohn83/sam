from django.urls import path

from . import views

urlpatterns = [
    path("stats/admissions/", views.AdmissionStatsView.as_view()),
    path("stats/seats/", views.SeatFillStatsView.as_view()),
    path("stats/revenue/", views.RevenueStatsView.as_view()),
    path("stats/agents/", views.AgentPerformanceView.as_view()),
    path("stats/verification/", views.VerificationPerformanceView.as_view()),
    path("stats/trend/", views.AdmissionTrendView.as_view()),
    path("audit-trail/", views.AuditTrailView.as_view(), name="principal-audit-trail"),
    path("audit-trail/actions/", views.AuditTrailActionsView.as_view(), name="principal-audit-trail-actions"),
    path("audit-trail/export/", views.AuditTrailExportView.as_view(), name="principal-audit-trail-export"),
]

