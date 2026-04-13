from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from documents.models import OCRResult, Document
from admissions.models import Application
from .services import invalidate_application_confidence

def invalidate_queue_stats():
    cache.delete("verification:queue_stats")

@receiver(post_save, sender=OCRResult)
def handle_ocr_result_save(sender, instance, **kwargs):
    """
    Invalidate application confidence cache when a new OCR result is saved.
    """
    student = instance.document.student
    if hasattr(student, 'application'):
        invalidate_application_confidence(student.application.id)
    # Also invalidate global queue stats because avg confidence might change
    invalidate_queue_stats()


@receiver(post_save, sender=Document)
def handle_document_save(sender, instance, created, **kwargs):
    """
    Invalidate application confidence cache when a document is updated/re-uploaded.
    """
    if not created:
        student = instance.student
        if hasattr(student, 'application'):
            invalidate_application_confidence(student.application.id)
        invalidate_queue_stats()


@receiver(post_save, sender=Application)
def handle_application_save(sender, instance, created, **kwargs):
    """
    Invalidate global queue stats when an application is created or status changes.
    """
    invalidate_queue_stats()
