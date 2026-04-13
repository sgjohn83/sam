from django.urls import path

from .views import SendPushNotificationView, RegisterDeviceTokenView, UnregisterDeviceTokenView

urlpatterns = [
    path("send-push/", SendPushNotificationView.as_view(), name="send-push"),
    path("device-tokens/", RegisterDeviceTokenView.as_view(), name="register-device-token"),
    path("device-tokens/unregister/", UnregisterDeviceTokenView.as_view(), name="unregister-device-token"),
]
