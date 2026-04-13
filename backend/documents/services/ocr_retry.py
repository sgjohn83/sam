import logging
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

from documents.models import Document, DocumentStatus
from .ocr_service import process_document
from .ocr_exceptions import OCRProcessingError, OCREmptyResultError


logger = logging.getLogger("ocr")

RETRY_KEY_PREFIX = "ocr:retries"
PROCESSING_LOCK_PREFIX = "ocr:processing"
MAX_RETRIES = 3
STALE_MINUTES = 10
RETRY_COUNTER_TTL_SECONDS = 60 * 60 * 24  # 24h


def _retry_key(document_id) -> str:
    return f"{RETRY_KEY_PREFIX}:{document_id}"


def _processing_key(document_id) -> str:
    return f"{PROCESSING_LOCK_PREFIX}:{document_id}"


def _get_retry_count(document_id) -> int:
    value = cache.get(_retry_key(document_id))
    return int(value) if value is not None else 0


def _increment_retry_count(document_id) -> int:
    key = _retry_key(document_id)
    value = cache.get(key)
    if value is None:
        cache.set(key, 1, timeout=RETRY_COUNTER_TTL_SECONDS)
        return 1
    new_count = int(value) + 1
    cache.set(key, new_count, timeout=RETRY_COUNTER_TTL_SECONDS)
    return new_count


def _set_processing_lock(document_id):
    cache.set(_processing_key(document_id), "in_progress", timeout=300)


def _clear_processing_lock(document_id):
    cache.delete(_processing_key(document_id))


def retry_failed_documents():
    """
    Find documents stuck in 'processing' for >10 minutes and retry OCR.
    Max 3 retries tracked in Redis.
    """
    cutoff = timezone.now() - timedelta(minutes=STALE_MINUTES)
    stuck_docs = Document.objects.filter(
        status=DocumentStatus.PROCESSING,
        uploaded_at__lt=cutoff,
    ).order_by("uploaded_at")

    summary = {
        "checked": stuck_docs.count(),
        "retried": 0,
        "succeeded": 0,
        "failed": 0,
        "skipped_max_retries": 0,
        "skipped_in_progress": 0,
    }

    for doc in stuck_docs:
        if cache.get(_processing_key(doc.id)) is not None:
            summary["skipped_in_progress"] += 1
            continue

        current_retries = _get_retry_count(doc.id)
        if current_retries >= MAX_RETRIES:
            summary["skipped_max_retries"] += 1
            logger.error(
                "OCR retries exhausted for document=%s retries=%d; leaving status=processing. Admin notified.",
                doc.id,
                current_retries,
            )
            continue

        attempt = _increment_retry_count(doc.id)
        summary["retried"] += 1
        _set_processing_lock(doc.id)
        try:
            process_document(doc.id)
            summary["succeeded"] += 1
            logger.info(
                "OCR retry succeeded: document=%s attempt=%d",
                doc.id,
                attempt,
            )
        except (OCRProcessingError, OCREmptyResultError) as exc:
            summary["failed"] += 1
            logger.error(
                "OCR retry failed: document=%s attempt=%d error=%s",
                doc.id,
                attempt,
                str(exc),
            )
        except Exception as exc:
            summary["failed"] += 1
            logger.exception(
                "Unexpected OCR retry failure: document=%s attempt=%d error=%s",
                doc.id,
                attempt,
                str(exc),
            )
        finally:
            _clear_processing_lock(doc.id)

    return summary
