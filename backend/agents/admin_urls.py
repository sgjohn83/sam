from django.urls import path
from . import views

urlpatterns = [
    path('commissions/', views.AdminCommissionListView.as_view(), name="admin-commission-list"),
    path('commissions/<uuid:pk>/approve/', views.CommissionApproveView.as_view(), name="admin-commission-approve"),
    path('commissions/<uuid:pk>/reject/', views.CommissionRejectView.as_view(), name="admin-commission-reject"),
    path('commissions/<uuid:pk>/mark-paid/', views.CommissionMarkPaidView.as_view(), name="admin-commission-mark-paid"),
    path('commissions/bulk-pay/', views.BulkPayCommissionsView.as_view(), name="admin-commission-bulk-pay"),
]
