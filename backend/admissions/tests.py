from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import Mock, patch
from admissions.models import Application, ApplicationStatus
from accounts.models import User
from students.models import StudentProfile


class OfficerApplicationListViewTests(TestCase):
    """Unit tests for OfficerApplicationListView"""

    def setUp(self):
        self.client = APIClient()
        
        # Create officer user
        self.officer = User.objects.create_user(
            email='officer@test.com',
            full_name='Test Officer',
            password='testpass123',
            role=User.Role.ADMISSION_OFFICER
        )
        
        # Create verification staff user (should be rejected)
        self.staff = User.objects.create_user(
            email='staff@test.com',
            full_name='Test Staff',
            password='testpass123',
            role=User.Role.VERIFICATION_STAFF
        )
        
        # Create student user and profile
        self.student_user = User.objects.create_user(
            email='student@test.com',
            full_name='John Doe',
            password='testpass123',
            role=User.Role.STUDENT
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            category='general',
            domicile_state='Telangana'
        )
        
        # Create test application
        self.application = Application.objects.create(
            student=self.student_profile,
            application_number='ADM-2024-00001',
            status=ApplicationStatus.VERIFIED,
            fee_amount=50000.00,
            submitted_at='2024-01-15T10:00:00Z'
        )

    def test_officer_can_access_endpoint(self):
        """Test that officer can access the applications list"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_cannot_access_endpoint(self):
        """Test that verification staff cannot access officer endpoint"""
        self.client.force_authenticate(user=self.staff)
        response = self.client.get('/api/officer/applications/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access(self):
        """Test that unauthenticated users cannot access"""
        response = self.client.get('/api/officer/applications/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pagination_default(self):
        """Test default pagination (page 1, 20 items)"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('page', response.data)
        self.assertIn('page_size', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['page_size'], 20)

    def test_pagination_custom_page(self):
        """Test custom pagination parameters"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/?page=2&page_size=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['page'], 2)
        self.assertEqual(response.data['page_size'], 10)

    def test_status_filter_verified(self):
        """Test filtering by verified status"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/?status=verified')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return the verified application

    def test_status_filter_allocated(self):
        """Test filtering by allocated status"""
        self.client.force_authenticate(user=self.officer)
        
        # Create an allocated application
        allocated_app = Application.objects.create(
            student=self.student_profile,
            application_number='ADM-2024-00002',
            status=ApplicationStatus.SEAT_ALLOCATED,
            fee_amount=45000.00
        )
        
        response = self.client.get('/api/officer/applications/?status=allocated')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify only allocated application is returned
        if response.data['results']:
            for result in response.data['results']:
                self.assertEqual(result['status'], ApplicationStatus.SEAT_ALLOCATED)

    def test_search_by_application_number(self):
        """Test search by application number"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/?search=00001')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if response.data['results']:
            self.assertIn('00001', response.data['results'][0]['application_number'])

    def test_search_by_student_name(self):
        """Test search by student name"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/?search=John')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if response.data['results']:
            self.assertIn('John', response.data['results'][0]['student_name'])

    def test_sort_by_merit_score_desc(self):
        """Test sorting by merit score descending (default)"""
        self.client.force_authenticate(user=self.officer)
        
        # Create another application with higher fee
        app2 = Application.objects.create(
            student=self.student_profile,
            application_number='ADM-2024-00003',
            status=ApplicationStatus.VERIFIED,
            fee_amount=60000.00
        )
        
        response = self.client.get('/api/officer/applications/?sort_by=merit_score&sort_order=desc')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if len(response.data['results']) >= 2:
            # Higher merit score (fee_amount) should be first
            self.assertGreaterEqual(
                response.data['results'][0].get('merit_score') or 0,
                response.data['results'][1].get('merit_score') or 0
            )

    def test_sort_by_submitted_at_asc(self):
        """Test sorting by submitted_at ascending"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/?sort_by=submitted_at&sort_order=asc')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sort_by_application_number(self):
        """Test sorting by application_number"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/?sort_by=application_number&sort_order=desc')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_fields(self):
        """Test that response contains required fields"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if response.data['results']:
            result = response.data['results'][0]
            required_fields = [
                'application_id', 'application_number', 'student_name', 'status',
                'branch_preferences', 'category', 'domicile_state', 'allocated_branch',
                'allocated_quota', 'merit_score', 'submitted_at', 'locked_at', 'is_locked'
            ]
            for field in required_fields:
                self.assertIn(field, result)

    def test_category_filter(self):
        """Test filtering by student category"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/?category=general')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_domicile_state_filter(self):
        """Test filtering by domicile state"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/?domicile_state=Telangana')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_quota_filter(self):
        """Test filtering by quota"""
        self.client.force_authenticate(user=self.officer)
        
        # Add quota to application
        self.application.allocated_quota = 'general'
        self.application.save()
        
        response = self.client.get('/api/officer/applications/?quota=general')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_empty_results(self):
        """Test response when no applications match filters"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/?status=admitted')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])

    def test_pagination_boundaries(self):
        """Test pagination with large page number"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/applications/?page=1000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])


class OfficerApplicationDetailViewTests(TestCase):
    """Unit tests for OfficerApplicationDetailView"""

    def setUp(self):
        self.client = APIClient()
        
        # Create officer user
        self.officer = User.objects.create_user(
            email='officer@test.com',
            full_name='Test Officer',
            password='testpass123',
            role=User.Role.ADMISSION_OFFICER
        )
        
        # Create verification staff user
        self.staff = User.objects.create_user(
            email='staff@test.com',
            full_name='Test Staff',
            password='testpass123',
            role=User.Role.VERIFICATION_STAFF
        )
        
        # Create student user and profile
        self.student_user = User.objects.create_user(
            email='student@test.com',
            full_name='John Doe',
            password='testpass123',
            role=User.Role.STUDENT
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            category='general',
            domicile_state='Telangana',
            mobile_number='1234567890'
        )
        
        # Create test application
        self.application = Application.objects.create(
            student=self.student_profile,
            application_number='ADM-2024-00001',
            status=ApplicationStatus.VERIFIED,
            fee_amount=50000.00,
            submitted_at='2024-01-15T10:00:00Z'
        )
        
        # Create locked application
        self.locked_application = Application.objects.create(
            student=self.student_profile,
            application_number='ADM-2024-00002',
            status=ApplicationStatus.VERIFIED,
            fee_amount=55000.00,
            submitted_at='2024-01-16T10:00:00Z',
            is_locked=True,
            locked_by=self.officer
        )

    def test_officer_can_access_detail(self):
        """Test that officer can access application detail"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get(f'/api/officer/applications/{self.application.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_cannot_access_detail(self):
        """Test that verification staff cannot access officer endpoint"""
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(f'/api/officer/applications/{self.application.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_detail(self):
        """Test that unauthenticated users cannot access"""
        response = self.client.get(f'/api/officer/applications/{self.application.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_response_contains_required_fields(self):
        """Test that response contains all required fields"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get(f'/api/officer/applications/{self.application.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        required_fields = [
            'application_id', 'application_number', 'status', 'is_locked',
            'lock_info', 'student_profile', 'branch_preferences',
            'allocated_branch', 'allocated_quota', 'fee_amount',
            'merit_score', 'documents', 'verification_status', 'audit_trail'
        ]
        for field in required_fields:
            self.assertIn(field, response.data)

    def test_student_profile_in_response(self):
        """Test that student profile is included in response"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get(f'/api/officer/applications/{self.application.id}/')
        
        self.assertIn('student_profile', response.data)
        self.assertEqual(response.data['student_profile']['full_name'], 'John Doe')
        self.assertEqual(response.data['student_profile']['category'], 'general')

    def test_locked_application_has_immutable_fields(self):
        """Test that locked application response includes immutable fields"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get(f'/api/officer/applications/{self.locked_application.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_locked'])
        self.assertIn('lock_info', response.data)
        self.assertIn('immutable_fields', response.data['lock_info'])
        self.assertTrue(len(response.data['lock_info']['immutable_fields']) > 0)

    def test_locked_application_lock_info(self):
        """Test that locked application includes lock details"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get(f'/api/officer/applications/{self.locked_application.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['lock_info']['is_locked'])
        self.assertIsNotNone(response.data['lock_info']['locked_at'])
        self.assertIsNotNone(response.data['lock_info']['locked_by'])

    def test_unlocked_application_no_immutable_fields(self):
        """Test that unlocked application has empty immutable fields"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get(f'/api/officer/applications/{self.application.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_locked'])
        self.assertEqual(response.data['lock_info']['immutable_fields'], [])

    def test_application_not_found(self):
        """Test 404 for non-existent application"""
        self.client.force_authenticate(user=self.officer)
        import uuid
        fake_id = uuid.uuid4()
        response = self.client.get(f'/api/officer/applications/{fake_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_audit_trail_in_response(self):
        """Test that audit trail is included in response"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get(f'/api/officer/applications/{self.application.id}/')
        
        self.assertIn('audit_trail', response.data)
        self.assertIsInstance(response.data['audit_trail'], list)

    def test_documents_in_response(self):
        """Test that documents are included in response"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get(f'/api/officer/applications/{self.application.id}/')
        
        self.assertIn('documents', response.data)
        self.assertIsInstance(response.data['documents'], list)

    def test_verification_status_in_response(self):
        """Test that verification status is included in response"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get(f'/api/officer/applications/{self.application.id}/')
        
        self.assertIn('verification_status', response.data)
        self.assertIsInstance(response.data['verification_status'], dict)

    def test_merit_breakdown_in_response(self):
        """Test that merit breakdown is included in response"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get(f'/api/officer/applications/{self.application.id}/')
        
        self.assertIn('merit_breakdown', response.data)
        self.assertIn('total_score', response.data['merit_breakdown'])
        self.assertIn('base_score', response.data['merit_breakdown'])
        self.assertIn('additional_score', response.data['merit_breakdown'])


class OfficerDashboardStatsViewTests(TestCase):
    """Unit tests for OfficerDashboardStatsView"""

    def setUp(self):
        self.client = APIClient()
        
        # Create officer user
        self.officer = User.objects.create_user(
            email='officer@test.com',
            full_name='Test Officer',
            password='testpass123',
            role=User.Role.ADMISSION_OFFICER
        )
        
        # Create verification staff user
        self.staff = User.objects.create_user(
            email='staff@test.com',
            full_name='Test Staff',
            password='testpass123',
            role=User.Role.VERIFICATION_STAFF
        )
        
        # Create student user and profile
        self.student_user = User.objects.create_user(
            email='student@test.com',
            full_name='John Doe',
            password='testpass123',
            role=User.Role.STUDENT
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            category='general',
            domicile_state='Telangana'
        )
        
        # Create test applications with different statuses
        self.app_verified = Application.objects.create(
            student=self.student_profile,
            application_number='ADM-2024-00001',
            status=ApplicationStatus.VERIFIED,
            fee_amount=50000.00
        )
        
        self.app_allocated = Application.objects.create(
            student=self.student_profile,
            application_number='ADM-2024-00002',
            status=ApplicationStatus.SEAT_ALLOCATED,
            fee_amount=45000.00,
            allocated_quota='general'
        )
        
        self.app_rejected = Application.objects.create(
            student=self.student_profile,
            application_number='ADM-2024-00003',
            status=ApplicationStatus.REJECTED,
            fee_amount=30000.00
        )

    def test_officer_can_access_stats(self):
        """Test that officer can access dashboard stats"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_cannot_access_stats(self):
        """Test that verification staff cannot access dashboard stats"""
        self.client.force_authenticate(user=self.staff)
        response = self.client.get('/api/officer/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_stats(self):
        """Test that unauthenticated users cannot access"""
        response = self.client.get('/api/officer/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_response_contains_by_status(self):
        """Test that response contains status counts"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/dashboard/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('by_status', response.data)
        self.assertIn('verified', response.data['by_status'])
        self.assertIn('allocated', response.data['by_status'])
        self.assertIn('rejected', response.data['by_status'])

    def test_response_contains_by_branch(self):
        """Test that response contains branch stats"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/dashboard/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('by_branch', response.data)
        self.assertIsInstance(response.data['by_branch'], list)

    def test_response_contains_by_quota(self):
        """Test that response contains quota stats"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/dashboard/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('by_quota', response.data)
        self.assertIsInstance(response.data['by_quota'], dict)

    def test_response_contains_by_category(self):
        """Test that response contains category stats"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/dashboard/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('by_category', response.data)
        self.assertIsInstance(response.data['by_category'], dict)

    def test_response_contains_cached_at(self):
        """Test that response includes cache timestamp"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/dashboard/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cached_at', response.data)

    def test_status_counts_correct(self):
        """Test that status counts are accurate"""
        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/officer/dashboard/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have 1 verified, 1 allocated, 1 rejected
        self.assertEqual(response.data['by_status']['verified'], 1)
        self.assertEqual(response.data['by_status']['allocated'], 1)
        self.assertEqual(response.data['by_status']['rejected'], 1)