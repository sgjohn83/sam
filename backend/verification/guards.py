from rest_framework import status
from rest_framework.response import Response
from django.utils import timezone
from admissions.models import Application, ApplicationStatus
from accounts.models import User


class ApplicationLockGuard:
    """
    Guard service that enforces immutability on locked applications.
    Returns 423 Locked for unauthorized write operations.
    """

    ALLOWED_ACTIONS_AFTER_LOCK = {
        'unlock': [User.Role.ADMIN],
        'admin_unlock': [User.Role.ADMIN],
        'seat_allocation': [User.Role.ADMISSION_OFFICER, User.Role.ADMIN],
        'fee_update': [User.Role.ADMISSION_OFFICER, User.Role.ADMIN],
        'status_change': [User.Role.ADMISSION_OFFICER, User.Role.ADMIN],
        'allocate_seat': [User.Role.ADMISSION_OFFICER, User.Role.ADMIN],
        'update_fee': [User.Role.ADMISSION_OFFICER, User.Role.ADMIN],
    }

    LOCKED_STATUSES = [
        ApplicationStatus.VERIFIED,
        ApplicationStatus.SEAT_ALLOCATED,
        ApplicationStatus.FEE_PENDING,
        ApplicationStatus.ADMITTED,
    ]

    @classmethod
    def check_lock(cls, application, action=None, user=None):
        """
        Check if application is locked and if the action is allowed.
        
        Args:
            application: Application instance
            action: Optional action name being performed
            user: User performing the action
            
        Returns:
            tuple: (is_allowed: bool, response: Response or None)
        """
        if not application.is_locked:
            return True, None

        if user and cls._is_action_allowed(action, user):
            return True, None

        return False, cls._locked_response(application)

    @classmethod
    def _is_action_allowed(cls, action, user):
        if not action:
            return False
            
        allowed_roles = cls.ALLOWED_ACTIONS_AFTER_LOCK.get(action, [])
        
        if user.is_superuser or user.role == User.Role.ADMIN:
            return True
            
        return user.role in allowed_roles

    @classmethod
    def _locked_response(cls, application):
        lock_info = {
            'error': 'Application is locked',
            'message': 'This application has been locked and cannot be modified.',
            'locked_at': application.locked_at.isoformat() if application.locked_at else None,
            'locked_by': application.locked_by.email if application.locked_by else None,
        }
        return Response(lock_info, status=status.HTTP_423_LOCKED)

    @classmethod
    def can_unlock(cls, user):
        """Check if user has permission to unlock applications."""
        return user.is_superuser or user.role == User.Role.ADMIN

    @classmethod
    def can_allocate_seat(cls, user):
        """Check if user has permission to allocate seats on locked applications."""
        return user.is_superuser or user.role in [User.Role.ADMIN, User.Role.ADMISSION_OFFICER]

    @classmethod
    def can_update_fee(cls, user):
        """Check if user has permission to update fee on locked applications."""
        return user.is_superuser or user.role in [User.Role.ADMIN, User.Role.ADMISSION_OFFICER]

    @classmethod
    def can_change_status(cls, user):
        """Check if user has permission to change status on locked applications."""
        return user.is_superuser or user.role in [User.Role.ADMIN, User.Role.ADMISSION_OFFICER]


def check_application_lock(application, action=None, user=None):
    """
    Convenience function to check application lock status.
    Use this in views before performing write operations.
    
    Example:
        is_allowed, response = check_application_lock(application, 'field_edit', request.user)
        if not is_allowed:
            return response
    """
    return ApplicationLockGuard.check_lock(application, action, user)