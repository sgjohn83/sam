from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = 'Seeds initial System Admin'

    def handle(self, *args, **kwargs):
        if not User.objects.filter(email='admin@college.edu').exists():
            User.objects.create_superuser(
                email='admin@college.edu',
                full_name='System Admin',
                password='adminpassword'
            )
            self.stdout.write(self.style.SUCCESS('Successfully created admin user'))
        else:
            self.stdout.write('Admin user already exists')
