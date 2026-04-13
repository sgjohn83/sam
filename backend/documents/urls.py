from django.urls import path
from .views import (
    DocumentUploadView,
    DocumentReuploadView,
    DocumentListView,
    DocumentDetailView,
    DocumentFileView,
    DocumentOCRResultView,
    DocumentOCRHistoryView,
)

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='doc-upload'),
    path('<uuid:pk>/reupload/', DocumentReuploadView.as_view(), name='doc-reupload'),
    path('', DocumentListView.as_view(), name='doc-list'),
    path('<uuid:pk>/', DocumentDetailView.as_view(), name='doc-detail'),
    path('<uuid:pk>/file/', DocumentFileView.as_view(), name='doc-file'),
    path('<uuid:pk>/ocr-result/', DocumentOCRResultView.as_view(), name='doc-ocr-result'),
    path('<uuid:pk>/ocr-history/', DocumentOCRHistoryView.as_view(), name='doc-ocr-history'),
]
