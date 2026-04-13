from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from admissions.models import Application, ApplicationStatus
from notifications.tasks import send_notification
from .models import CommissionRecord, CommissionStatus

@receiver(post_save, sender=Application)
def handle_admission_commission(sender, instance, created, **kwargs):
    """
    Automatically create a commission record when a student is admitted.
    """
    if instance.status == ApplicationStatus.ADMITTED:
        student = instance.student
        if not student or not student.agent:
            return

        # Check if commission already exists
        if CommissionRecord.objects.filter(application=instance).exists():
            return

        agent_profile = student.agent
        fee_amount = instance.fee_amount or 0
        rate = agent_profile.commission_rate
        amount = (fee_amount * rate) / 100

        # Create record within a transaction
        with transaction.atomic():
            commission = CommissionRecord.objects.create(
                agent=agent_profile,
                application=instance,
                student=student,
                fee_amount=fee_amount,
                commission_rate=rate,
                commission_amount=amount,
                status=CommissionStatus.PENDING
            )

            # Skip notification if commission is 0 (Edge Case 3)
            if amount > 0:
                send_notification.delay(
                    notification_type='commission_created',
                    user_id=str(agent_profile.user_id),
                    context={
                        'email': agent_profile.user.email,
                        'agent_name': agent_profile.agency_name or agent_profile.user.full_name,
                        'student_name': student.user.full_name,
                        'amount': str(amount),
                    }
                )
