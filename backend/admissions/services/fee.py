from django.utils import timezone
from django.conf import settings

from notifications.tasks import send_notification


def notify_fee_payment(application):
    """Called after seat allocation sets status=fee_pending."""
    deadline = application.fee_deadline  # DateTimeField set during allocation
    
    # Calculate fee details
    from admissions.views import calculate_fee
    fee_data = calculate_fee(application.id)
    
    if not fee_data:
        # Fallback to basic fee calculation
        total = float(application.fee_amount or 0)
        concession = float(application.fee_concession or 0)
        net_payable = max(total - concession, 0)
        fee_data = {
            'line_items': [{
                'fee_type': 'Tuition Fee',
                'total': total
            }],
            'total': total,
            'concession': concession,
            'net_payable': net_payable
        }
    
    send_notification.delay(
        notification_type='fee_payment_request',
        user_id=str(application.student.user_id),
        context={
            'student_name': application.student.user.full_name,
            'application_number': application.application_number,
            'branch_name': application.allocated_branch.name,
            'branch_code': application.allocated_branch.code,
            'quota': application.get_allocated_quota_display(),
            'fee_amount': str(fee_data['total']),
            'fee_concession': str(fee_data['concession']),
            'fee_final': str(fee_data['net_payable']),
            'deadline': deadline.strftime('%d %B %Y, %I:%M %p'),
            'payment_link': f'{settings.MOBILE_APP_SCHEME}://fee-payment/{application.id}',
            'support_email': 'admissions@college.edu',
            'related_object_id': str(application.id),
        },
    )


def notify_admission_confirmation(application):
    """Called after payment confirmation sets status=admitted."""
    # Get configurable next-steps from current AcademicYear
    from administration.models import AcademicYear
    
    try:
        current_year = AcademicYear.objects.get(is_current=True)
        orientation_date = current_year.orientation_date
        orientation_venue = current_year.orientation_venue
        reporting_date = current_year.reporting_date
    except AcademicYear.DoesNotExist:
        # Fallback values if no current academic year is set
        orientation_date = None
        orientation_venue = 'Main Campus Auditorium'
        reporting_date = None
    
    # Format dates for display
    orientation_date_str = str(orientation_date) if orientation_date else 'To be announced'
    reporting_date_str = str(reporting_date) if reporting_date else 'To be announced'
    orientation_venue_str = str(orientation_venue) if orientation_venue else 'Main Campus Auditorium'
    
    # Calculate fee paid amount
    fee_paid_amount = float(application.fee_amount or 0) - float(application.fee_concession or 0)
    
    send_notification.delay(
        notification_type='admission_confirmed',
        user_id=str(application.student.user_id),
        context={
            'student_name': application.student.user.full_name,
            'application_number': application.application_number,
            'branch_name': application.allocated_branch.name,
            'branch_code': application.allocated_branch.code,
            'quota': application.get_allocated_quota_display(),
            'fee_paid_amount': str(fee_paid_amount),
            'admitted_date': application.admitted_at.strftime('%d %B %Y'),
            'academic_year': current_year.year_label if 'current_year' in locals() else '2024-25',
            'orientation_date': orientation_date_str,
            'orientation_venue': orientation_venue_str,
            'reporting_date': reporting_date_str,
            'dashboard_link': f'{settings.MOBILE_APP_SCHEME}://dashboard',
            'support_email': 'admissions@college.edu',
            'contact_info': 'admissions@college.edu | +91-XXXXXXXXXX',
            'related_object_id': str(application.id),
        },
    )