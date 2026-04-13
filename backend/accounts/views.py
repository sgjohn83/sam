from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from .models import OTPVerification, generate_otp, User
from notifications.utils import send_email_with_retry
from django.utils import timezone
from datetime import timedelta
import requests


def _has_profile(user: User) -> bool:
    return hasattr(user, "student_profile")


def _application_status(user: User) -> str:
    # Application model is not yet finalized; keep conservative default.
    return "draft"


class GoogleAuthView(APIView):
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify token with Google
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        response = requests.get(url)
        if response.status_code != 200:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_info = response.json()
        email = user_info.get('email')
        google_id = user_info.get('sub')
        full_name = user_info.get('name')

        # Find or create user
        user, created = User.objects.get_or_create(email=email, defaults={
            'full_name': full_name,
            'google_sso_id': google_id,
            'role': User.Role.STUDENT
        })

        if not created and not user.google_sso_id:
            user.google_sso_id = google_id
            user.save()

        # Update last_login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        auth_token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': auth_token.key,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'has_profile': _has_profile(user),
            'application_status': _application_status(user),
        }, status=status.HTTP_200_OK)

class RegisterView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Rate limit: 3 OTPs per hour
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_otps = OTPVerification.objects.filter(email=email, created_at__gte=one_hour_ago).count()
        if recent_otps >= 3:
            return Response({'error': 'Too many requests, try again later'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        otp_code = generate_otp()
        expires_at = timezone.now() + timedelta(minutes=10)
        OTPVerification.objects.create(email=email, otp_code=otp_code, expires_at=expires_at)

        # Send email with retry logic
        subject = "Your OTP for Admission Portal"
        body = f"Your OTP is {otp_code}. It will expire in 10 minutes."
        success = send_email_with_retry(subject, body, [email])
        
        if success:
            return Response({'message': 'OTP sent'}, status=status.HTTP_200_OK)
        return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        
        otp_obj = OTPVerification.objects.filter(email=email, is_verified=False).order_by('-created_at').first()
        if not otp_obj or otp_obj.expires_at < timezone.now():
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        if otp_obj.attempts >= 5:
            return Response({'error': 'Too many failed attempts'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.otp_code != code:
            otp_obj.attempts += 1
            otp_obj.save()
            return Response({'error': f'Invalid code, {5 - otp_obj.attempts} attempts left'}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj.is_verified = True
        otp_obj.save()
        
        # Create user if not exists
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': 'New Student',
                'role': User.Role.STUDENT,
            }
        )
        auth_token, _ = Token.objects.get_or_create(user=user)
        
        return Response(
            {
                'message': 'Verified',
                'token': auth_token.key,
                'user': {
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'has_profile': _has_profile(user),
                }
            },
            status=status.HTTP_200_OK
        )

from .serializers import UserSerializer

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CheckEmailView(APIView):
    def get(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        exists = User.objects.filter(email=email).exists()
        return Response({'exists': exists}, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
