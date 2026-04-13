from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import User

class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_roles(self):
        roles = [User.Role.STUDENT, User.Role.VERIFICATION_STAFF, User.Role.ADMIN]
        for role in roles:
            user = User.objects.create(email=f"{role}@test.com", full_name="Test User", role=role)
            self.assertEqual(user.role, role)

    def test_register_otp_flow(self):
        response = self.client.post(reverse('register'), {'email': 'test@test.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify OTP
        # We need to get the OTP code from the DB
        from accounts.models import OTPVerification
        otp = OTPVerification.objects.get(email='test@test.com')
        
        # Success
        response = self.client.post(reverse('verify-otp'), {'email': 'test@test.com', 'code': otp.otp_code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
