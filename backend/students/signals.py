from django.db.models.signals import post_save
from django.dispatch import receiver

from admissions.models import Application
from students.models import StudentProfile


@receiver(post_save, sender=StudentProfile)
def create_application_on_profile(sender, instance, created, **kwargs):
    if created:
        Application.objects.create(student=instance)
