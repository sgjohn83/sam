"""
Email notification service for fee-related notifications.
"""
from django.utils import timezone
from ..tasks import send_notification
from ..models import NotificationLog
import logging

logger = logging.getLogger(__name__)


def send_fee_payment_request(application, fee_data, deadline_days=7):
    """
    Send initial fee payment request notification.
    
    Args:
        application: Application object
        fee_data: Dictionary with fee breakdown
        deadline_days: Number of days for payment deadline
    """
    from students.models import StudentProfile
    
    try:
        student = StudentProfile.objects.get(id=application.student_id)
        user = student.user
        
        # Calculate deadline date
        deadline_date = timezone.now() + timezone.timedelta(days=deadline_days)
        
        context = {
            'student_name': user.full_name,
            'application_number': application.application_number,
            'branch_name': application.allocated_branch,
            'quota': application.allocated_quota,
            'line_items': fee_data.get('line_items', []),
            'total': fee_data.get('total', 0),
            'concession': fee_data.get('concession', 0),
            'net_payable': fee_data.get('net_payable', 0),
            'payment_reference': application.payment_reference_id,
            'fee_deadline': deadline_date.strftime('%d %B %Y'),
            'fee_amount': fee_data.get('net_payable', 0),
            'deadline': deadline_date.strftime('%d %B %Y'),
            'bank_details': {
                'account_name': 'College Admission Account',
                'account_number': '123456789012',
                'ifsc_code': 'SBIN0001234',
                'bank_name': 'State Bank of India',
            },
            'contact_info': 'Admissions Office: admissions@college.edu | Phone: 040-12345678',
            'related_object_id': str(application.id),
            'email': user.email,
        }
        
        # Send notification asynchronously
        send_notification.delay(
            notification_type='fee_payment_request',
            user_id=str(user.id),
            context=context,
        )
        
        logger.info(f"Fee payment request queued for application {application.application_number}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to queue fee payment request for application {application.application_number}: {e}")
        return False


def send_fee_payment_reminder(application, fee_data, days_remaining):
    """
    Send fee payment reminder notification.
    
    Args:
        application: Application object
        fee_data: Dictionary with fee breakdown
        days_remaining: Days remaining until deadline
    """
    from students.models import StudentProfile
    
    try:
        student = StudentProfile.objects.get(id=application.student_id)
        user = student.user
        
        context = {
            'student_name': user.full_name,
            'application_number': application.application_number,
            'branch_name': application.allocated_branch,
            'net_payable': fee_data.get('net_payable', 0),
            'payment_reference': application.payment_reference_id,
            'fee_deadline': application.fee_deadline.strftime('%d %B %Y') if application.fee_deadline else 'N/A',
            'days_remaining': days_remaining,
            'fee_amount': fee_data.get('net_payable', 0),
            'contact_info': 'Admissions Office: admissions@college.edu | Phone: 040-12345678',
            'related_object_id': str(application.id),
            'email': user.email,
        }
        
        # Send notification asynchronously
        send_notification.delay(
            notification_type='fee_payment_reminder',
            user_id=str(user.id),
            context=context,
        )
        
        logger.info(f"Fee payment reminder queued for application {application.application_number}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to queue fee payment reminder for application {application.application_number}: {e}")
        return False


def send_admission_confirmed_notification(application):
    """
    Send admission confirmed notification after payment.
    
    Args:
        application: Application object
    """
    from students.models import StudentProfile
    
    try:
        student = StudentProfile.objects.get(id=application.student_id)
        user = student.user
        
        context = {
            'student_name': user.full_name,
            'application_number': application.application_number,
            'branch_name': application.allocated_branch,
            'quota': application.allocated_quota,
            'admitted_at': timezone.now().strftime('%d %B %Y'),
            'contact_info': 'Admissions Office: admissions@college.edu | Phone: 040-12345678',
            'related_object_id': str(application.id),
            'email': user.email,
        }
        
        # Send notification asynchronously
        send_notification.delay(
            notification_type='admission_confirmed',
            user_id=str(user.id),
            context=context,
        )
        
        logger.info(f"Admission confirmed notification queued for application {application.application_number}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to queue admission confirmed notification for application {application.application_number}: {e}")
        return False