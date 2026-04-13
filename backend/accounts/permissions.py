from rest_framework.permissions import BasePermission
from accounts.models import User

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == User.Role.STUDENT or request.user.is_superuser)

class IsVerificationStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == User.Role.VERIFICATION_STAFF or request.user.is_superuser)

class IsAdmissionOfficer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == User.Role.ADMISSION_OFFICER or request.user.is_superuser)

class IsAgent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == User.Role.AGENT or request.user.is_superuser)

class IsPrincipal(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == User.Role.PRINCIPAL or request.user.is_superuser)

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


def check_officer_role(user):
    """
    Helper function to check if user has admission officer role.
    Returns True for officers, admins, and superusers.
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    if hasattr(user, 'role') and user.role == User.Role.ADMIN:
        return True
    
    return hasattr(user, 'role') and user.role == User.Role.ADMISSION_OFFICER


def check_verification_or_officer_role(user):
    """
    Helper function to check if user has verification staff or admission officer role.
    Returns True for verification staff, officers, admins, and superusers.
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    if hasattr(user, 'role'):
        allowed_roles = [
            User.Role.VERIFICATION_STAFF,
            User.Role.ADMISSION_OFFICER,
            User.Role.ADMIN,
        ]
        return user.role in allowed_roles
    
    return False


def officer_required(view_func):
    """
    Decorator to restrict a view to admission officers only.
    Usage:
        @officer_required
        def my_view(request):
            ...
    """
    from rest_framework.response import Response
    
    def wrapped(request, *args, **kwargs):
        if not check_officer_role(request.user):
            return Response(
                {'error': 'You must be an Admission Officer to perform this action.'},
                status=403
            )
        return view_func(request, *args, **kwargs)
    return wrapped


def verification_staff_or_officer_required(view_func):
    """
    Decorator to restrict a view to verification staff or admission officers.
    Usage:
        @verification_staff_or_officer_required
        def my_view(request):
            ...
    """
    from rest_framework.response import Response
    
    def wrapped(request, *args, **kwargs):
        if not check_verification_or_officer_role(request.user):
            return Response(
                {'error': 'You must be a Verification Staff or Admission Officer to perform this action.'},
                status=403
            )
        return view_func(request, *args, **kwargs)
    return wrapped
