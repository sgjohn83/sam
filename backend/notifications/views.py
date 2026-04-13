from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from accounts.models import User
from .models import DeviceToken
from .serializers import DeviceTokenSerializer
from .utils import send_push_to_student


class SendPushNotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not (request.user.is_superuser or request.user.role == User.Role.ADMIN):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        student_user_id = request.data.get("student_user_id")
        title = request.data.get("title")
        body = request.data.get("body")
        data = request.data.get("data", {})

        if not student_user_id or not title or not body:
            return Response(
                {"error": "student_user_id, title and body are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = send_push_to_student(student_user_id, title, body, data=data)
        return Response(
            {"message": "Push dispatch attempted", "result": result},
            status=status.HTTP_200_OK,
        )


class RegisterDeviceTokenView(generics.CreateAPIView):
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]


class UnregisterDeviceTokenView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        token = request.data.get('expo_push_token')
        DeviceToken.objects.filter(
            user=request.user, expo_push_token=token
        ).update(is_active=False)
        return Response(status=status.HTTP_204_NO_CONTENT)
