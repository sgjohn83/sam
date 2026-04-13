from django.db import migrations
from django.utils import timezone


def create_test_officer_user(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    if User.objects.filter(email='officer@test.edu').exists():
        return

    User.objects.create(
        email='officer@test.edu',
        full_name='Test Admission Officer',
        role='admission_officer',
        is_staff=False,
        is_active=True,
    )


def remove_test_officer_user(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(email='officer@test.edu').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_test_officer_user,
            remove_test_officer_user
        ),
    ]