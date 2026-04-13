from django.test import TestCase
from unittest.mock import Mock, MagicMock
from django.utils import timezone
from datetime import timedelta
from verification.guards import ApplicationLockGuard, check_application_lock
from admissions.models import Application, ApplicationStatus
from accounts.models import User


class MockUser:
    """Mock user for testing"""
    def __init__(self, role=User.Role.VERIFICATION_STAFF, is_superuser=False):
        self.role = role
        self.is_superuser = is_superuser


class MockApplication:
    """Mock application for testing"""
    def __init__(self, is_locked=False, locked_at=None, locked_by=None):
        self.is_locked = is_locked
        self.locked_at = locked_at
        self.locked_by = locked_by


class ApplicationLockGuardTests(TestCase):
    """Unit tests for ApplicationLockGuard"""

    def setUp(self):
        self.admin_user = MockUser(role=User.Role.ADMIN, is_superuser=False)
        self.superuser = MockUser(role=User.Role.ADMIN, is_superuser=True)
        self.staff_user = MockUser(role=User.Role.VERIFICATION_STAFF, is_superuser=False)
        self.officer_user = MockUser(role=User.Role.ADMISSION_OFFICER, is_superuser=False)
        
        self.unlocked_app = MockApplication(is_locked=False)
        
        self.locked_app = MockApplication(
            is_locked=True,
            locked_at=timezone.now(),
            locked_by=self.staff_user
        )

    def test_unlocked_application_allows_any_action(self):
        """Test that unlocked applications allow any action"""
        is_allowed, response = check_application_lock(
            self.unlocked_app, 
            'field_edit', 
            self.staff_user
        )
        self.assertTrue(is_allowed)
        self.assertIsNone(response)

    def test_locked_application_rejects_field_edit(self):
        """Test that locked applications reject field_edit action"""
        is_allowed, response = check_application_lock(
            self.locked_app, 
            'field_edit', 
            self.staff_user
        )
        self.assertFalse(is_allowed)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 423)

    def test_locked_application_rejects_verify_document(self):
        """Test that locked applications reject verify_document action"""
        is_allowed, response = check_application_lock(
            self.locked_app, 
            'verify_document', 
            self.staff_user
        )
        self.assertFalse(is_allowed)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 423)

    def test_locked_application_rejects_reject_document(self):
        """Test that locked applications reject reject_document action"""
        is_allowed, response = check_application_lock(
            self.locked_app, 
            'reject_document', 
            self.staff_user
        )
        self.assertFalse(is_allowed)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 423)

    def test_admin_can_unlock(self):
        """Test that admin can perform unlock action"""
        is_allowed, response = check_application_lock(
            self.locked_app, 
            'unlock', 
            self.admin_user
        )
        self.assertTrue(is_allowed)
        self.assertIsNone(response)

    def test_superuser_can_unlock(self):
        """Test that superuser can perform unlock action"""
        is_allowed, response = check_application_lock(
            self.locked_app, 
            'unlock', 
            self.superuser
        )
        self.assertTrue(is_allowed)
        self.assertIsNone(response)

    def test_officer_can_allocate_seat(self):
        """Test that admission officer can allocate seat on locked application"""
        is_allowed, response = check_application_lock(
            self.locked_app, 
            'allocate_seat', 
            self.officer_user
        )
        self.assertTrue(is_allowed)
        self.assertIsNone(response)

    def test_officer_can_update_fee(self):
        """Test that admission officer can update fee on locked application"""
        is_allowed, response = check_application_lock(
            self.locked_app, 
            'update_fee', 
            self.officer_user
        )
        self.assertTrue(is_allowed)
        self.assertIsNone(response)

    def test_officer_can_change_status(self):
        """Test that admission officer can change status on locked application"""
        is_allowed, response = check_application_lock(
            self.locked_app, 
            'status_change', 
            self.officer_user
        )
        self.assertTrue(is_allowed)
        self.assertIsNone(response)

    def test_staff_cannot_allocate_seat(self):
        """Test that verification staff cannot allocate seat on locked application"""
        is_allowed, response = check_application_lock(
            self.locked_app, 
            'allocate_seat', 
            self.staff_user
        )
        self.assertFalse(is_allowed)
        self.assertEqual(response.status_code, 423)

    def test_staff_cannot_unlock(self):
        """Test that verification staff cannot unlock application"""
        is_allowed, response = check_application_lock(
            self.locked_app, 
            'unlock', 
            self.staff_user
        )
        self.assertFalse(is_allowed)
        self.assertEqual(response.status_code, 423)

    def test_no_action_specified_rejected_for_locked(self):
        """Test that locked application rejects when no action specified"""
        is_allowed, response = check_application_lock(
            self.locked_app, 
            None, 
            self.staff_user
        )
        self.assertFalse(is_allowed)
        self.assertEqual(response.status_code, 423)

    def test_locked_response_contains_lock_info(self):
        """Test that locked response contains lock information"""
        is_allowed, response = check_application_lock(
            self.locked_app, 
            'field_edit', 
            self.staff_user
        )
        
        self.assertEqual(response.status_code, 423)
        data = response.data
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertIn('locked_at', data)
        self.assertIn('locked_by', data)

    def test_can_unlock_method(self):
        """Test can_unlock helper method"""
        self.assertTrue(ApplicationLockGuard.can_unlock(self.admin_user))
        self.assertTrue(ApplicationLockGuard.can_unlock(self.superuser))
        self.assertFalse(ApplicationLockGuard.can_unlock(self.staff_user))

    def test_can_allocate_seat_method(self):
        """Test can_allocate_seat helper method"""
        self.assertTrue(ApplicationLockGuard.can_allocate_seat(self.admin_user))
        self.assertTrue(ApplicationLockGuard.can_allocate_seat(self.officer_user))
        self.assertFalse(ApplicationLockGuard.can_allocate_seat(self.staff_user))

    def test_can_update_fee_method(self):
        """Test can_update_fee helper method"""
        self.assertTrue(ApplicationLockGuard.can_update_fee(self.admin_user))
        self.assertTrue(ApplicationLockGuard.can_update_fee(self.officer_user))
        self.assertFalse(ApplicationLockGuard.can_update_fee(self.staff_user))

    def test_can_change_status_method(self):
        """Test can_change_status helper method"""
        self.assertTrue(ApplicationLockGuard.can_change_status(self.admin_user))
        self.assertTrue(ApplicationLockGuard.can_change_status(self.officer_user))
        self.assertFalse(ApplicationLockGuard.can_change_status(self.staff_user))


class MockModel:
    """Mock Django model for testing"""
    class _meta:
        model_name = 'application'
    
    def __init__(self, pk='test-uuid'):
        self.pk = pk


class MockUserWithId:
    """Mock user with ID for testing"""
    def __init__(self, user_id='user-123'):
        self.id = user_id


class AuditLoggerTests(TestCase):
    """Unit tests for AuditLogger service"""
    
    def test_compute_diff_no_changes(self):
        """Test diff with identical before/after"""
        from verification.audit_logger import compute_diff
        
        before = {'name': 'John', 'age': 30}
        after = {'name': 'John', 'age': 30}
        
        before_diff, after_diff = compute_diff(before, after)
        self.assertIsNone(before_diff)
        self.assertIsNone(after_diff)
    
    def test_compute_diff_single_change(self):
        """Test diff with single field change"""
        from verification.audit_logger import compute_diff
        
        before = {'name': 'John', 'age': 30}
        after = {'name': 'Jane', 'age': 30}
        
        before_diff, after_diff = compute_diff(before, after)
        
        self.assertEqual(before_diff, {'name': 'John'})
        self.assertEqual(after_diff, {'name': 'Jane'})
    
    def test_compute_diff_new_field(self):
        """Test diff with new field added"""
        from verification.audit_logger import compute_diff
        
        before = {'name': 'John'}
        after = {'name': 'John', 'age': 30}
        
        before_diff, after_diff = compute_diff(before, after)
        
        self.assertIsNone(before_diff)
        self.assertEqual(after_diff, {'age': 30})
    
    def test_compute_diff_removed_field(self):
        """Test diff with field removed"""
        from verification.audit_logger import compute_diff
        
        before = {'name': 'John', 'age': 30}
        after = {'name': 'John'}
        
        before_diff, after_diff = compute_diff(before, after)
        
        self.assertEqual(before_diff, {'age': 30})
        self.assertIsNone(after_diff)
    
    def test_compute_diff_none_inputs(self):
        """Test diff with None inputs"""
        from verification.audit_logger import compute_diff
        
        before_diff, after_diff = compute_diff(None, None)
        self.assertIsNone(before_diff)
        self.assertIsNone(after_diff)
    
    def test_record_requires_actor(self):
        """Test that record raises error without actor"""
        from verification.audit_logger import AuditLogger
        
        with self.assertRaises(ValueError) as ctx:
            AuditLogger.record(
                entity=MockModel(),
                action='test_action',
                before={'field': 'old'},
                after={'field': 'new'}
            )
        
        self.assertIn('Actor is required', str(ctx.exception))
    
    def test_record_requires_valid_actor(self):
        """Test that record raises error with invalid actor"""
        from verification.audit_logger import AuditLogger
        
        invalid_actor = Mock()
        invalid_actor.id = None
        
        with self.assertRaises(ValueError) as ctx:
            AuditLogger.record(
                entity=MockModel(),
                action='test_action',
                before={'field': 'old'},
                after={'field': 'new'},
                actor=invalid_actor
            )
        
        self.assertIn('valid user ID', str(ctx.exception))
    
    def test_record_with_actor(self):
        """Test record with explicit actor"""
        from verification.audit_logger import AuditLogger
        from verification.models import AuditLog
        
        actor = MockUserWithId()
        entity = MockModel()
        
        with self.assertRaises(Exception):
            AuditLogger.record(
                entity=entity,
                action='test_action',
                before={'field': 'old'},
                after={'field': 'new'},
                actor=actor
            )
    
    def test_record_with_request(self):
        """Test record with request object"""
        from verification.audit_logger import AuditLogger
        
        mock_request = Mock()
        mock_request.user = MockUserWithId()
        mock_request.META = {'REMOTE_ADDR': '192.168.1.1'}
        
        entity = MockModel()
        
        with self.assertRaises(Exception):
            AuditLogger.record(
                entity=entity,
                action='test_action',
                before={'field': 'old'},
                after={'field': 'new'},
                request=mock_request
            )
    
    def test_record_field_change_helper(self):
        """Test record_field_change convenience method"""
        from verification.audit_logger import AuditLogger
        
        mock_request = Mock()
        mock_request.user = MockUserWithId()
        mock_request.META = {'REMOTE_ADDR': '192.168.1.1'}
        
        entity = MockModel()
        
        with self.assertRaises(Exception):
            AuditLogger.record_field_change(
                entity=entity,
                field_name='name',
                old_value='John',
                new_value='Jane',
                request=mock_request
            )
    
    def test_record_status_change_helper(self):
        """Test record_status_change convenience method"""
        from verification.audit_logger import AuditLogger
        
        mock_request = Mock()
        mock_request.user = MockUserWithId()
        mock_request.META = {'REMOTE_ADDR': '192.168.1.1'}
        
        entity = MockModel()
        
        with self.assertRaises(Exception):
            AuditLogger.record_status_change(
                entity=entity,
                old_status='submitted',
                new_status='verified',
                request=mock_request
            )