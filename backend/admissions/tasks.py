from celery import shared_task
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging
from .models import Application, ApplicationStatus
from notifications.tasks import send_notification

logger = logging.getLogger(__name__)

REMINDER_DAYS = [3, 1]  # Send reminders at 3 days and 1 day before deadline


@shared_task
def send_fee_payment_reminders():
    """
    Run daily via Celery Beat. Sends reminders for applications
    with fee_pending status approaching their payment deadline.
    """
    now = timezone.now()
    total_reminders = 0

    for days in REMINDER_DAYS:
        target_date = (now + timedelta(days=days)).date()
        applications = Application.objects.filter(
            status=ApplicationStatus.FEE_PENDING,
            fee_paid=False,
            fee_deadline__date=target_date,
        ).select_related('student__user', 'allocated_branch')

        logger.info(f"Checking for {days}-day reminders on {target_date}: {applications.count()} applications found")
        
        for app in applications:
            # Skip if payment reference is missing (shouldn't happen for fee_pending apps)
            if not app.payment_reference_id:
                continue
                
            send_notification.delay(
                notification_type='fee_payment_reminder',
                user_id=str(app.student.user_id),
                context={
                    'email': app.student.user.email,
                    'student_name': app.student.user.full_name,
                    'application_number': app.application_number,
                    'branch_name': app.allocated_branch.name,
                    'branch_code': app.allocated_branch.code,
                    'quota': app.get_allocated_quota_display(),
                    'fee_amount': str(app.fee_amount),
                    'fee_concession': str(app.fee_concession),
                    'fee_final': str(app.fee_amount - app.fee_concession),
                    'deadline': app.fee_deadline.strftime('%d %B %Y'),
                    'days_remaining': str(days),
                    'payment_link': f'{settings.MOBILE_APP_SCHEME}://fee-payment/{app.id}',
                    'original_sent_date': app.fee_instruction_sent_at.strftime('%d %B %Y') if app.fee_instruction_sent_at else 'Previously',
                    'support_email': 'admissions@college.edu',
                    'related_object_id': str(app.id),
                },
            )
            total_reminders += 1
            logger.info(f"Queued {days}-day reminder for {app.application_number} ({app.student.user.email})")
    
    logger.info(f"Fee payment reminders task completed. Sent {total_reminders} reminders.")


@shared_task
def send_overdue_fee_notifications():
    """
    Run daily via Celery Beat. Sends notifications for applications
    with fee_pending status that have passed their payment deadline.
    
    Only sends notifications once per week for the same application
    to avoid spamming students.
    """
    now = timezone.now()
    one_week_ago = now - timedelta(days=7)
    
    # Find applications where deadline has passed but fee is still pending
    overdue_applications = Application.objects.filter(
        status=ApplicationStatus.FEE_PENDING,
        fee_paid=False,
        fee_deadline__lt=now,
    ).select_related('student__user', 'allocated_branch')
    
    logger.info(f"Found {overdue_applications.count()} overdue applications needing notification")
    
    for app in overdue_applications:
        # Skip if payment reference is missing
        if not app.payment_reference_id:
            continue
            
        # Calculate days overdue
        days_overdue = (now.date() - app.fee_deadline.date()).days
        
        send_notification.delay(
            notification_type='fee_payment_overdue',
            user_id=str(app.student.user_id),
            context={
                'email': app.student.user.email,
                'student_name': app.student.user.full_name,
                'application_number': app.application_number,
                'branch_name': app.allocated_branch.name,
                'branch_code': app.allocated_branch.code,
                'quota': app.get_allocated_quota_display(),
                'fee_amount': str(app.fee_amount),
                'fee_concession': str(app.fee_concession),
                'net_payable': str(app.fee_amount - app.fee_concession),
                'payment_reference': app.payment_reference_id,
                'fee_deadline': app.fee_deadline.strftime('%d %B %Y'),
                'days_overdue': str(days_overdue),
                'payment_link': f'{settings.MOBILE_APP_SCHEME}://fee-payment/{app.id}',
                'contact_info': 'admissions@college.edu | +91-XXXXXXXXXX',
                'related_object_id': str(app.id),
            },
        )
        logger.info(f"Queued overdue notification for {app.application_number} ({days_overdue} days overdue)")
    
    logger.info(f"Overdue fee notifications task completed. Sent {overdue_applications.count()} notifications.")