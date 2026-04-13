from django.urls import path
from .views import GoogleAuthView, RegisterView, VerifyOTPView, MeView, LogoutView, CheckEmailView

urlpatterns = [
    path('auth/google/', GoogleAuthView.as_view(), name='google_auth'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/check-email/', CheckEmailView.as_view(), name='check-email'),
    path('check-email/', CheckEmailView.as_view(), name='check-email-public'),
]
