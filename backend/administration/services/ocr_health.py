from django.conf import settings
from django.db.models import Avg, Count, Max, Q
from django.utils import timezone

from documents.models import Document, DocumentStatus, OCRResult


def get_ocr_stats() -> dict:
    """Aggregate OCR metrics from OCRResult table."""
    today = timezone.localdate()
    today_ocr_qs = OCRResult.objects.filter(created_at__date=today)
    today_documents_qs = Document.objects.filter(uploaded_at__date=today)

    total_requests_today = today_ocr_qs.count()
    average_duration_ms = (
        float(today_ocr_qs.aggregate(avg=Avg("processing_duration_ms"))["avg"] or 0.0)
    )
    slowest_request_ms = int(
        today_ocr_qs.aggregate(max=Max("processing_duration_ms"))["max"] or 0
    )
    average_confidence = float(
        today_ocr_qs.aggregate(avg=Avg("overall_confidence"))["avg"] or 0.0
    )

    error_count_today = today_documents_qs.filter(
        status=DocumentStatus.PROCESSING
    ).count()
    total_documents_today = today_documents_qs.count()
    error_rate_percent = (
        (error_count_today / total_documents_today) * 100.0
        if total_documents_today
        else 0.0
    )

    by_status = Document.objects.aggregate(
        processing=Count("id", filter=Q(status=DocumentStatus.PROCESSING)),
        extracted=Count("id", filter=Q(status=DocumentStatus.EXTRACTED)),
        verified=Count("id", filter=Q(status=DocumentStatus.VERIFIED)),
        rejected=Count("id", filter=Q(status=DocumentStatus.REJECTED)),
    )

    return {
        "total_requests_today": total_requests_today,
        "average_duration_ms": round(average_duration_ms, 2),
        "error_count_today": error_count_today,
        "error_rate_percent": round(error_rate_percent, 2),
        "slowest_request_ms": slowest_request_ms,
        "average_confidence": round(average_confidence, 4),
        "documents_by_status": {
            "processing": by_status["processing"],
            "extracted": by_status["extracted"],
            "verified": by_status["verified"],
            "rejected": by_status["rejected"],
        },
        "model_used": settings.GEMINI_MODEL,
    }
