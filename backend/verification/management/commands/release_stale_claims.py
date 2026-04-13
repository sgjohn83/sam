from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from admissions.models import Application

class Command(BaseCommand):
    help = 'Auto-releases stale application claims older than 30 minutes.'

    def handle(self, *args, **options):
        thirty_min_ago = timezone.now() - timedelta(minutes=30)
        
        # Find applications claimed more than 30 minutes ago
        stale_applications = Application.objects.filter(
            claimed_by__isnull=False,
            claimed_at__lt=thirty_min_ago
        )
        
        count = stale_applications.count()
        if count > 0:
            # Clear claims
            stale_applications.update(
                claimed_by=None,
                claimed_at=None
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully released {count} stale claims."))
        else:
            self.stdout.write("No stale claims found.")
