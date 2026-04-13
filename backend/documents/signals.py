from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from documents.models import Document, DocumentStatus
from admissions.models import Application, ApplicationStatus
from notifications.models import Notification


@receiver(pre_save, sender=Document)
def store_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Document.objects.get(pk=instance.pk)
            instance._previous_status = old_instance.status
        except Document.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Document)
def bust_rejected_count_cache(sender, instance, **kwargs):
    try:
        if instance.student and instance.student.user_id:
            cache.delete(f"rejected_count:{instance.student.user_id}")
    except Exception:
        pass


@receiver(post_save, sender=Document)
def handle_document_reupload(sender, instance, created, **kwargs):
    if created:
        return

    try:
        if not hasattr(instance, '_previous_status'):
            return

        prev_status = instance._previous_status
        current_status = instance.status

        was_rejected = prev_status == DocumentStatus.REJECTED
        is_now_pending = current_status in [DocumentStatus.PROCESSING, DocumentStatus.EXTRACTED]

        if was_rejected and is_now_pending:
            _handle_reupload(instance)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in handle_document_reupload: {e}")


def _handle_reupload(document):
    from documents.models import DocumentType

    try:
        application = Application.objects.get(student=document.student)
    except Application.DoesNotExist:
        return

    document_type_display = DocumentType(document.document_type).label if document.document_type else document.document_type

    if application.claimed_by and application.claimed_at:
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        
        if application.claimed_at >= twenty_four_hours_ago:
            pass
        else:
            application.claimed_by = None
            application.claimed_at = None
            application.status = ApplicationStatus.SUBMITTED
            application.save(update_fields=['claimed_by', 'claimed_at', 'status'])
    else:
        if application.status == ApplicationStatus.UNDER_VERIFICATION:
            application.status = ApplicationStatus.SUBMITTED
            application.save(update_fields=['status'])

    if document.rejected_by:
        Notification.objects.create(
            recipient=document.rejected_by,
            notification_type='document_reupload',
            subject=f"Student re-uploaded {document_type_display}",
            body=f"Student re-uploaded {document_type_display} for application {application.application_number}. The document is now pending verification.",
            status='pending'
        )
