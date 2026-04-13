from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import OTPVerification

class Command(BaseCommand):
    help = 'Deletes OTPs older than 24 hours'

    def handle(self, *args, **kwargs):
        threshold = timezone.now() - timedelta(hours=24)
        count, _ = OTPVerification.objects.filter(created_at__lt=threshold).delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} expired OTPs'))
