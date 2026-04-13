import uuid

from django.db import models
from django.db.models import F, Q


class AcademicYear(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    year_label = models.CharField(max_length=10, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    admission_open_date = models.DateField()
    admission_close_date = models.DateField()
    is_current = models.BooleanField(default=False)
    # Configurable next-steps for admission confirmation emails
    orientation_date = models.DateField(null=True, blank=True, help_text="Date of orientation program")
    orientation_venue = models.CharField(max_length=200, blank=True, help_text="Venue for orientation program")
    reporting_date = models.DateField(null=True, blank=True, help_text="Date for reporting to college")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["is_current"],
                condition=Q(is_current=True),
                name="uniq_current_academic_year",
            )
        ]

    def __str__(self):
        return self.year_label

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self._create_seat_matrix()

    def _create_seat_matrix(self):
        from django.db import transaction

        branches = Branch.objects.filter(is_active=True)
        if not branches.exists():
            return

        existing_combos = set(
            SeatMatrix.objects.filter(academic_year=self).values_list("branch_id", "quota")
        )

        to_create = []
        for branch in branches:
            for quota, _label in QuotaType.choices:
                if (branch.id, quota) not in existing_combos:
                    to_create.append(SeatMatrix(
                        branch=branch,
                        academic_year=self,
                        quota=quota,
                        total_seats=0,
                        allocated_seats=0,
                    ))

        if to_create:
            SeatMatrix.objects.bulk_create(to_create, ignore_conflicts=True)


class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class QuotaType(models.TextChoices):
    GENERAL = "general", "General"
    OBC = "obc", "OBC"
    SC = "sc", "SC"
    ST = "st", "ST"
    MANAGEMENT = "management", "Management"
    NRI = "nri", "NRI"


class SeatMatrix(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    quota = models.CharField(max_length=20, choices=QuotaType.choices)
    total_seats = models.IntegerField()
    allocated_seats = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "academic_year", "quota"],
                name="uniq_branch_year_quota",
            ),
            models.CheckConstraint(
                check=Q(allocated_seats__lte=F("total_seats")),
                name="allocated_lte_total_seats",
            ),
            models.CheckConstraint(
                check=Q(total_seats__gte=0),
                name="total_seats_gte_zero",
            ),
            models.CheckConstraint(
                check=Q(allocated_seats__gte=0),
                name="allocated_seats_gte_zero",
            ),
        ]

    def __str__(self):
        return f"{self.branch.code} {self.academic_year.year_label} {self.quota}"
