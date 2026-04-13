from django.urls import path
from .views import (
    AgentDashboardView, AgentStudentListView, AgentStudentDetailView,
    AgentCommissionListView, AgentRegisterStudentView,
    AgentProfileView, AgentProfileCompletionView,
    AgentPipelineSummaryView, AgentCommissionSummaryView,
    AdminCommissionListView, CommissionApproveView, CommissionRejectView,
    CommissionMarkPaidView, BulkPayCommissionsView, AdminAgentListView,
)

urlpatterns = [
    # Agent endpoints
    path('dashboard/', AgentDashboardView.as_view(), name='agent-dashboard'),
    path('students/', AgentStudentListView.as_view(), name='agent-students'),
    path('students/<uuid:pk>/', AgentStudentDetailView.as_view(), name='agent-student-detail'),
    path('commissions/', AgentCommissionListView.as_view(), name='agent-commissions'),
    path('register-student/', AgentRegisterStudentView.as_view(), name='agent-register-student'),
    path('profile/', AgentProfileView.as_view(), name='agent-profile'),
    path('profile/completion-status/', AgentProfileCompletionView.as_view(), name='agent-profile-completion'),
    path('pipeline-summary/', AgentPipelineSummaryView.as_view(), name='agent-pipeline-summary'),
    path('commission-summary/', AgentCommissionSummaryView.as_view(), name='agent-commission-summary'),

    # Admin commission management endpoints
    path('commissions/admin/', AdminCommissionListView.as_view(), name='admin-commissions'),
    path('commissions/<uuid:pk>/approve/', CommissionApproveView.as_view(), name='commission-approve'),
    path('commissions/<uuid:pk>/reject/', CommissionRejectView.as_view(), name='commission-reject'),
    path('commissions/<uuid:pk>/mark-paid/', CommissionMarkPaidView.as_view(), name='commission-mark-paid'),
    path('commissions/bulk-pay/', BulkPayCommissionsView.as_view(), name='commission-bulk-pay'),
    path('admin/', AdminAgentListView.as_view(), name='admin-agents'),
]
