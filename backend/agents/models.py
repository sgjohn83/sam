import uuid
from django.db import models
from django.conf import settings


class CommissionStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    PAID = 'paid', 'Paid'
    REJECTED = 'rejected', 'Rejected'


class AgentProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agent_profile',
        limit_choices_to={'role': 'agent'},
    )
    agency_name = models.CharField(max_length=300, null=True, blank=True)
    contact_phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.JSONField(null=True, blank=True)
    pan_number = models.CharField(max_length=10, null=True, blank=True)
    bank_account_name = models.CharField(max_length=200, null=True, blank=True)
    bank_account_number = models.CharField(max_length=30, null=True, blank=True)
    bank_ifsc = models.CharField(max_length=11, null=True, blank=True)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00,
        help_text="Percentage of fee amount"
    )
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='verified_agents',
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    total_students_referred = models.IntegerField(default=0)
    total_commission_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_verified', 'is_active']),
        ]

    def __str__(self):
        return f"{self.agency_name or self.user.full_name} ({self.user.email})"


class CommissionRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name='commissions')
    application = models.OneToOneField(
        'admissions.Application',
        on_delete=models.CASCADE,
        related_name='commission',
    )
    student = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='commission_records',
    )
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=CommissionStatus.choices,
        default=CommissionStatus.PENDING,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='approved_commissions',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(commission_amount__gte=0),
                name='commission_amount_gte_zero',
            ),
        ]

    def __str__(self):
        return f"{self.agent} - {self.application.application_number} - ₹{self.commission_amount}"
