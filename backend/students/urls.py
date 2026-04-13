from django.urls import path

from .views import (
    StudentAutofillView,
    StudentProfileCompletionView,
    StudentProfileView,
    StudentPushTokenView,
    StudentStatusView,
    StudentRejectedDocumentsView,
    RejectedDocumentsCountView,
)

urlpatterns = [
    path("profile/", StudentProfileView.as_view(), name="student-profile"),
    path("profile/completion/", StudentProfileCompletionView.as_view(), name="student-profile-completion"),
    path("status/", StudentStatusView.as_view(), name="student-status"),
    path("autofill/", StudentAutofillView.as_view(), name="student-autofill"),
    path("push-token/", StudentPushTokenView.as_view(), name="student-push-token"),
    path("rejected-documents/", StudentRejectedDocumentsView.as_view(), name="student-rejected-documents"),
    path("rejected-documents/count/", RejectedDocumentsCountView.as_view(), name="student-rejected-documents-count"),
]
