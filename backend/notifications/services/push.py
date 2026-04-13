import logging
import requests
from typing import Iterable
from django.conf import settings
from ..models import DeviceToken, NotificationLog

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
EXPO_BATCH_SIZE = 100
EXPO_TIMEOUT = 10  # seconds


class ExpoPushError(Exception):
    pass


def _build_message(token: str, title: str, body: str, data: dict | None, sound: str = "default", channel_id: str = "default") -> dict:
    return {
        "to": token,
        "title": title,
        "body": body,
        "data": data or {},
        "sound": sound,
        "priority": "high",
        "channelId": channel_id,
    }


def _chunk(iterable: list, size: int) -> Iterable[list]:
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


def _send_batch(messages: list[dict]) -> list[dict]:
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json",
    }
    access_token = getattr(settings, "EXPO_ACCESS_TOKEN", None)
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    response = requests.post(
        EXPO_PUSH_URL,
        json=messages,
        headers=headers,
        timeout=EXPO_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("data", [])


def _handle_ticket_errors(tickets: list[dict], tokens: list[str]) -> None:
    for ticket, token in zip(tickets, tokens):
        if ticket.get("status") == "error":
            details = ticket.get("details", {}) or {}
            error_code = details.get("error")
            logger.warning(
                "Expo push error for token %s: %s (%s)",
                token[:20], ticket.get("message"), error_code,
            )
            if error_code == "DeviceNotRegistered":
                DeviceToken.objects.filter(expo_push_token=token).update(is_active=False)


def send_push_notification(
    user_id,
    title: str,
    body: str,
    data: dict | None = None,
) -> dict:
    """
    Send an Expo push notification to all active devices of a user.
    Returns {"sent": N, "failed": M, "no_devices": bool}.
    """
    tokens = list(
        DeviceToken.objects
        .filter(user_id=user_id, is_active=True)
        .values_list('expo_push_token', flat=True)
    )

    if not tokens:
        NotificationLog.objects.create(
            user_id=user_id,
            channel='push',
            template_name='',
            subject=title,
            body_preview=body[:200],
            status='failed',
            error='No active device tokens',
        )
        return {"sent": 0, "failed": 0, "no_devices": True}

    sent, failed = 0, 0
    for batch in _chunk(tokens, EXPO_BATCH_SIZE):
        messages = [_build_message(t, title, body, data) for t in batch]
        try:
            tickets = _send_batch(messages)
            _handle_ticket_errors(tickets, batch)
            sent += sum(1 for t in tickets if t.get("status") == "ok")
            failed += sum(1 for t in tickets if t.get("status") == "error")
        except (requests.RequestException, ExpoPushError) as e:
            logger.exception("Expo push batch failed: %s", e)
            failed += len(batch)
            NotificationLog.objects.create(
                user_id=user_id,
                channel='push',
                template_name='',
                subject=title,
                body_preview=body[:200],
                status='failed',
                error=str(e)[:500],
            )
            continue

        NotificationLog.objects.create(
            user_id=user_id,
            channel='push',
            template_name='',
            subject=title,
            body_preview=body[:200],
            status='sent' if failed == 0 else 'partial',
        )

    return {"sent": sent, "failed": failed, "no_devices": False}


def send_reupload_push_notification(user_id, document_type_label, application_number, document_id):
    """
    Send a push notification for document re-upload request.
    Uses the 'document_alerts' channel for Android.
    """
    title = "Document Re-upload Required"
    body = f"Please re-upload your {document_type_label} for application {application_number}"
    data = {
        "type": "document_reupload_request",
        "document_id": str(document_id),
    }
    
    tokens = list(
        DeviceToken.objects
        .filter(user_id=user_id, is_active=True)
        .values_list('expo_push_token', flat=True)
    )
    
    if not tokens:
        return {"sent": 0, "failed": 0, "no_devices": True}
    
    sent, failed = 0, 0
    for batch in _chunk(tokens, EXPO_BATCH_SIZE):
        messages = [_build_message(t, title, body, data, channel_id="document_alerts") for t in batch]
        try:
            tickets = _send_batch(messages)
            _handle_ticket_errors(tickets, batch)
            sent += sum(1 for t in tickets if t.get("status") == "ok")
            failed += sum(1 for t in tickets if t.get("status") == "error")
        except (requests.RequestException, ExpoPushError) as e:
            logger.exception("Expo push batch failed: %s", e)
            failed += len(batch)
            continue
    
    return {"sent": sent, "failed": failed, "no_devices": False}
