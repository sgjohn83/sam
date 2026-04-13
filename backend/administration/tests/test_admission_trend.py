from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from admissions.models import Application, ApplicationStatus
from students.models import StudentProfile


class AdmissionTrendViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.principal = User.objects.create_user(
            email="principal.trend@test.com",
            full_name="Principal Trend",
            password="testpass123",
            role=User.Role.PRINCIPAL,
        )
        self.staff = User.objects.create_user(
            email="staff.trend@test.com",
            full_name="Staff Trend",
            password="testpass123",
            role=User.Role.VERIFICATION_STAFF,
        )
        self._student_seq = 0

    def _create_application(self, status, submitted_at=None, admitted_at=None):
        self._student_seq += 1
        student_user = User.objects.create_user(
            email=f"student{self._student_seq}@test.com",
            full_name=f"Student {self._student_seq}",
            password="testpass123",
            role=User.Role.STUDENT,
        )
        profile = StudentProfile.objects.create(
            user=student_user,
            mobile_number=f"90000000{self._student_seq:02d}",
            category="general",
            domicile_state="Telangana",
        )
        return Application.objects.create(
            student=profile,
            status=status,
            submitted_at=submitted_at,
            admitted_at=admitted_at,
        )

    def test_principal_can_fetch_admission_trend(self):
        now = timezone.now()
        self._create_application(
            status=ApplicationStatus.SUBMITTED,
            submitted_at=now - timedelta(days=2),
        )
        self._create_application(
            status=ApplicationStatus.ADMITTED,
            submitted_at=now - timedelta(days=4),
            admitted_at=now - timedelta(days=1),
        )
        self._create_application(status=ApplicationStatus.REJECTED)

        self.client.force_authenticate(user=self.principal)
        response = self.client.get("/api/principal/stats/trend/?period=daily&days=30")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["period"], "daily")
        self.assertIn("submitted", response.data)
        self.assertIn("admitted", response.data)
        self.assertIn("rejected", response.data)
        self.assertEqual(sum(item["count"] for item in response.data["submitted"]), 2)
        self.assertEqual(sum(item["count"] for item in response.data["admitted"]), 1)
        self.assertEqual(sum(item["count"] for item in response.data["rejected"]), 1)

    def test_invalid_period_returns_400(self):
        self.client.force_authenticate(user=self.principal)
        response = self.client.get("/api/principal/stats/trend/?period=hourly")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_days_returns_400(self):
        self.client.force_authenticate(user=self.principal)
        response = self.client.get("/api/principal/stats/trend/?days=0")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_principal_role_forbidden(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get("/api/principal/stats/trend/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
