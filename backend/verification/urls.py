from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VerificationQueueViewSet, SplitScreenViewSet, DocumentReuploadHistoryViewSet, ApplicationAuditLogsViewSet

router = DefaultRouter()
router.register(r'queue', VerificationQueueViewSet, basename='verification-queue')

urlpatterns = [
    path('', include(router.urls)),
    path('<uuid:pk>/split-screen/', SplitScreenViewSet.as_view({'get': 'retrieve'}), name='split-screen'),
    path('<uuid:pk>/field/', SplitScreenViewSet.as_view({'patch': 'field_edit'}), name='field-edit'),
    path('documents/<uuid:pk>/reupload-history/', DocumentReuploadHistoryViewSet.as_view({'get': 'retrieve'}), name='document-reupload-history'),
    path('applications/<uuid:pk>/audit-logs/', ApplicationAuditLogsViewSet.as_view({'get': 'retrieve'}), name='application-audit-logs'),
]
