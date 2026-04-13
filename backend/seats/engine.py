from django.db import transaction
from django.db.models import F
from django.core.exceptions import PermissionDenied
from django.core.cache import cache

from administration.models import AcademicYear, SeatMatrix
from admissions.models import Application, ApplicationStatus
from verification.models import AuditLog
from accounts.models import User


class SeatUnavailableError(Exception):
    """Raised when no seats are available for allocation."""
    pass


class SeatAlreadyAllocatedError(Exception):
    """Raised when application already has a seat allocated."""
    pass


def allocate_seat(application_id, branch_id, quota, actor=None):
    """
    Atomically allocate a seat to an application.
    
    Uses SELECT FOR UPDATE to prevent race conditions.
    
    Args:
        application_id: UUID of the application
        branch_id: UUID of the branch to allocate
        quota: quota type (e.g., 'general', 'obc', 'management')
        actor: user performing the allocation (for audit log)
    
    Returns:
        Application object if successful
    
    Raises:
        SeatUnavailableError: if no seats available
        Application.DoesNotExist: if application not found
        Branch.DoesNotExist: if branch not found
    """
    with transaction.atomic():
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            raise SeatUnavailableError("No current academic year")

        seat_row = SeatMatrix.objects.select_for_update().filter(
            academic_year=current_year,
            branch_id=branch_id,
            quota=quota,
        ).first()

        if not seat_row:
            from administration.models import Branch
            raise SeatUnavailableError(f"No seat matrix for branch {branch_id} quota {quota}")

        if seat_row.allocated_seats >= seat_row.total_seats:
            raise SeatUnavailableError(
                f"No seats available for {seat_row.branch.name} ({quota}). "
                f"Allocated: {seat_row.allocated_seats}/{seat_row.total_seats}"
            )

        application = Application.objects.select_for_update().get(pk=application_id)

        if application.status != ApplicationStatus.VERIFIED:
            raise SeatUnavailableError(
                f"Application must be verified, current status: {application.status}"
            )

        if application.allocated_branch_id:
            raise SeatAlreadyAllocatedError(
                f"Application already allocated to {application.allocated_branch.name}"
            )

        application.allocated_branch_id = branch_id
        application.allocated_quota = quota
        application.status = ApplicationStatus.SEAT_ALLOCATED
        application.save(update_fields=[
            'allocated_branch', 'allocated_quota', 'status', 'updated_at'
        ])

        seat_row.allocated_seats = F('allocated_seats') + 1
        seat_row.save(update_fields=['allocated_seats'])

        _invalidate_seat_cache(branch_id, quota)

        _create_allocation_audit_log(
            application=application,
            branch_id=branch_id,
            quota=quota,
            action="allocate",
            actor=actor,
        )

    return application


def deallocate_seat(application_id, actor, reason):
    """
    Reverse (deallocate) a seat allocation.
    
    Args:
        application_id: UUID of the application
        actor: user performing the deallocation (must be admin/officer)
        reason: mandatory reason for deallocation
    
    Returns:
        Application object if successful
    
    Raises:
        PermissionDenied: if actor is not admin/officer or no reason provided
        Application.DoesNotExist: if application not found
    """
    if not actor.role in [User.Role.ADMIN, User.Role.OFFICER]:
        raise PermissionDenied("Only admin or officer can deallocate seats")

    if not reason or len(reason.strip()) < 10:
        raise PermissionDenied("Reason (min 10 chars) is required for deallocation")

    with transaction.atomic():
        application = Application.objects.select_for_update().get(pk=application_id)

        if not application.allocated_branch_id:
            raise SeatUnavailableError("No seat allocated to this application")

        branch_id = application.allocated_branch_id
        quota = application.allocated_quota

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year:
            seat_row = SeatMatrix.objects.select_for_update().filter(
                academic_year=current_year,
                branch_id=branch_id,
                quota=quota,
            ).first()

            if seat_row:
                seat_row.allocated_seats = F('allocated_seats') - 1
                seat_row.save(update_fields=['allocated_seats'])

        application.allocated_branch = None
        application.allocated_quota = None
        application.status = ApplicationStatus.UNDER_VERIFICATION
        application.save(update_fields=[
            'allocated_branch', 'allocated_quota', 'status', 'updated_at'
        ])

        _invalidate_seat_cache(branch_id, quota)

        _create_allocation_audit_log(
            application=application,
            branch_id=branch_id,
            quota=quota,
            action="deallocate",
            actor=actor,
            reason=reason.strip(),
        )

    return application


def _invalidate_seat_cache(branch_id, quota):
    """Invalidate Redis cache for specific branch+quota."""
    cache.delete(f"seats:{branch_id}:{quota}")
    cache.delete("seats:summary")


def _create_allocation_audit_log(application, branch_id, quota, action, actor=None, reason=None):
    """Create audit log entry for allocation/deallocation."""
    before_json = {
        "allocated_branch": str(application.allocated_branch_id) if action == "deallocate" else None,
        "allocated_quota": application.allocated_quota if action == "deallocate" else None,
        "status": str(application.status) if action == "deallocate" else None,
    }
    after_json = {
        "allocated_branch": str(branch_id),
        "allocated_quota": quota,
        "status": ApplicationStatus.SEAT_ALLOCATED if action == "allocate" else None,
    }
    if reason:
        after_json["reason"] = reason

    AuditLog.objects.create(
        entity_type="application",
        entity_id=application.id,
        application=application,
        action=f"seat_{action}",
        user=actor,
        before_json=before_json,
        after_json=after_json,
    )