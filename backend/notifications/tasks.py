from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from .models import NotificationLog
from .registry import NOTIFICATION_TYPES
from .utils import send_push_to_student
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification(self, notification_type: str, user_id: str, context: dict):
    """
    Universal notification worker.

    Args:
        notification_type: key in NOTIFICATION_TYPES registry
        user_id: UUID of the recipient
        context: dict of template variables (must include 'email' key)
    """
    from accounts.models import User
    template_config = NOTIFICATION_TYPES.get(notification_type)
    if not template_config:
        logger.error("Unknown notification type: %s", notification_type)
        return

    user = User.objects.get(id=user_id)
    recipient_email = context.get('email') or user.email

    # ── Create or retrieve log entry ──
    log, created = NotificationLog.objects.get_or_create(
        user_id=user_id,
        template_name=notification_type,
        related_object_id=context.get('related_object_id'),
        channel='email',
        defaults={
            'subject': template_config.subject_template.format(**context),
            'body_preview': '',
            'status': 'pending',
        },
    )

    if not created and log.status == 'sent':
        logger.info("Notification already sent: %s for user %s", notification_type, user_id)
        return  # idempotency guard

    try:
        # ── Render email ──
        subject = template_config.subject_template.format(**context)
        support_email = getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL)
        html_body = render_to_string(
            f'emails/{template_config.template_name}.html',
            {**context, 'student_name': user.full_name, 'support_email': support_email},
        )
        text_body = render_to_string(
            f'emails/{template_config.template_name}.txt',
            {**context, 'student_name': user.full_name, 'support_email': support_email},
        )

        # ── Send email ──
        email_msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email_msg.attach_alternative(html_body, 'text/html')
        email_msg.send(fail_silently=False)

        # ── Update log: success ──
        log.status = 'sent'
        log.sent_at = timezone.now()
        log.subject = subject
        log.body_preview = text_body[:200]
        log.save()

        # ── Push notification (best-effort) ──
        if template_config.push_title and template_config.push_body_template:
            try:
                push_title = template_config.push_title.format(**context) if '{' in template_config.push_title else template_config.push_title
                push_body = template_config.push_body_template.format(**context) if '{' in template_config.push_body_template else template_config.push_body_template
                
                send_push_to_student(
                    student_user_id=user_id,
                    title=push_title,
                    body=push_body,
                    data={
                        'type': notification_type,
                        'related_object_id': context.get('related_object_id'),
                    },
                )
            except Exception as push_err:
                logger.warning("Push failed for %s: %s", notification_type, push_err)
                # Push failure does NOT retry the whole task

    except Exception as e:
        log.status = 'failed'
        log.error = str(e)[:500]
        log.retry_count = self.request.retries
        log.save()
        logger.exception("Email send failed for %s, user %s: %s", notification_type, user_id, e)
        raise self.retry(exc=e)