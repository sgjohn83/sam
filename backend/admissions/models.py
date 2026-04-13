import uuid

from django.conf import settings
from django.db import models


class ApplicationStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    UNDER_VERIFICATION = "under_verification", "Under Verification"
    VERIFIED = "verified", "Verified"
    SEAT_ALLOCATED = "seat_allocated", "Seat Allocated"
    FEE_PENDING = "fee_pending", "Fee Pending"
    ADMITTED = "admitted", "Admitted"
    REJECTED = "rejected", "Rejected"


class AdmissionChannel(models.TextChoices):
    ONLINE = "online", "Online"
    WALKIN = "walkin", "Walk-In"


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="application",
    )
    application_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(
        max_length=30,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
    )
    branch_preferences = models.JSONField(null=True, blank=True)
    submitted_data = models.JSONField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="locked_applications",
    )
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="claimed_applications",
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    allocated_branch = models.ForeignKey(
        "administration.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    allocated_quota = models.CharField(max_length=20, null=True, blank=True)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fee_concession = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee_paid = models.BooleanField(default=False)
    fee_paid_at = models.DateTimeField(null=True, blank=True)
    payment_proof_path = models.CharField(max_length=500, null=True, blank=True)
    admitted_at = models.DateTimeField(null=True, blank=True)
    
    admission_channel = models.CharField(
        max_length=10,
        choices=AdmissionChannel.choices,
        default=AdmissionChannel.ONLINE,
    )
    fee_deadline = models.DateTimeField(null=True, blank=True)
    payment_reference_id = models.CharField(max_length=50, null=True, blank=True)
    fee_instruction_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_application_number(self):
        from django.utils import timezone

        year = timezone.now().year
        last = Application.objects.filter(
            application_number__startswith=f"ADM-{year}-"
        ).count()
        return f"ADM-{year}-{str(last + 1).zfill(5)}"

    def save(self, *args, **kwargs):
        if not self.application_number:
            self.application_number = self.generate_application_number()
        super().save(*args, **kwargs)
