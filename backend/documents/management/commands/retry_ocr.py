from django.core.management.base import BaseCommand

from documents.services.ocr_retry import retry_failed_documents


class Command(BaseCommand):
    help = "Retry OCR for documents stuck in processing state for more than 10 minutes."

    def handle(self, *args, **options):
        summary = retry_failed_documents()
        self.stdout.write(
            self.style.SUCCESS(
                "retry_ocr completed: "
                f"checked={summary['checked']} "
                f"retried={summary['retried']} "
                f"succeeded={summary['succeeded']} "
                f"failed={summary['failed']} "
                f"skipped_max_retries={summary['skipped_max_retries']} "
                f"skipped_in_progress={summary['skipped_in_progress']}"
            )
        )
