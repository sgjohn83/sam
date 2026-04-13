import logging
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
import time
import requests

from students.models import PushToken

logger = logging.getLogger(__name__)

def send_email_with_retry(subject, body, recipient_list):
    max_retries = 3
    base_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            send_mail(
                subject,
                body,
                settings.EMAIL_HOST_USER,
                recipient_list,
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt)) # Exponential backoff
            else:
                return False


def send_push_to_student(student_user_id, title, body, data=None):
    """
    Send push notification to student's registered devices.
    Uses Expo Push API for Expo tokens. Other token providers can be added later.
    """
    tokens = PushToken.objects.filter(user_id=student_user_id)
    sent = 0
    failed = 0

    for push_token in tokens:
        message = {
            "to": push_token.token,
            "title": title,
            "body": body,
            "data": data or {},
            "sound": "default",
        }
        try:
            # Expo push token support (e.g., ExponentPushToken[...]).
            if push_token.token.startswith("ExponentPushToken["):
                response = requests.post(
                    "https://exp.host/--/api/v2/push/send",
                    json=message,
                    headers={
                        "Accept": "application/json",
                        "Accept-encoding": "gzip, deflate",
                        "Content-Type": "application/json",
                    },
                    timeout=10,
                )
                if 200 <= response.status_code < 300:
                    sent += 1
                else:
                    failed += 1
                    logger.error(
                        "Expo push failed for user_id=%s token_id=%s status=%s body=%s",
                        student_user_id,
                        push_token.id,
                        response.status_code,
                        response.text,
                    )
            else:
                # Placeholder for FCM/APNS token handling (future).
                failed += 1
                logger.warning(
                    "Unsupported push token format for user_id=%s token_id=%s",
                    student_user_id,
                    push_token.id,
                )
        except Exception as exc:
            failed += 1
            logger.exception(
                "Push notification error for user_id=%s token_id=%s error=%s",
                student_user_id,
                push_token.id,
                exc,
            )

    return {
        "token_count": tokens.count(),
        "sent": sent,
        "failed": failed,
    }
