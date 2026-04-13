from django.db import migrations
from django.utils import timezone
from datetime import timedelta
import uuid


def create_test_locked_application(apps, schema_editor):
    Application = apps.get_model('admissions', 'Application')
    User = apps.get_model('auth', 'User')
    StudentProfile = apps.get_model('students', 'StudentProfile')

    try:
        staff_user = User.objects.filter(role='verification_staff').first()
        if not staff_user:
            staff_user = User.objects.filter(is_staff=True).first()
        
        if not staff_user:
            print("No staff user found, skipping seed data")
            return

        student = StudentProfile.objects.first()
        if not student:
            print("No student profile found, skipping seed data")
            return

        application = Application.objects.filter(student=student).first()
        if not application:
            application = Application.objects.create(
                student=student,
                application_number=f"ADM-{timezone.now().year}-99999",
                status='submitted'
            )

        application.is_locked = True
        application.locked_at = timezone.now()
        application.locked_by = staff_user
        application.save(update_fields=['is_locked', 'locked_at', 'locked_by'])

        print(f"Created locked application: {application.application_number}")
    except Exception as e:
        print(f"Error creating seed data: {e}")


def remove_test_locked_application(apps, schema_editor):
    Application = apps.get_model('admissions', 'Application')
    
    try:
        Application.objects.filter(application_number__endswith='99999').delete()
        print("Removed test locked application")
    except Exception as e:
        print(f"Error removing seed data: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('admissions', '0002_application_submitted_data'),
    ]

    operations = [
        migrations.RunPython(
            create_test_locked_application,
            remove_test_locked_application
        ),
    ]