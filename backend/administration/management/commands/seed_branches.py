from django.core.management.base import BaseCommand
from administration.models import AcademicYear, Branch, SeatMatrix, QuotaType
from django.utils import timezone
from datetime import date

class Command(BaseCommand):
    help = 'Seeds branches and seat matrix for academic year 2026-27'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Academic Year...")
        
        # 1. Create Academic Year 2026-27
        ay, created = AcademicYear.objects.update_or_create(
            year_label="2026-27",
            defaults={
                "start_date": date(2026, 6, 1),
                "end_date": date(2027, 5, 31),
                "admission_open_date": date(2026, 1, 1),
                "admission_close_date": date(2026, 8, 31),
                "is_current": True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Academic Year: {ay.year_label}"))
        else:
            self.stdout.write(f"Updated Academic Year: {ay.year_label}")

        # 2. Define Branches and their Seat Matrix
        branches_data = {
            "CSE": {
                "name": "Computer Science and Engineering",
                "seats": {
                    QuotaType.GENERAL: 60,
                    QuotaType.OBC: 30,
                    QuotaType.SC: 15,
                    QuotaType.ST: 8,
                    QuotaType.MANAGEMENT: 10,
                    QuotaType.NRI: 5,
                }
            },
            "ECE": {
                "name": "Electronics and Communication Engineering",
                "seats": {
                    QuotaType.GENERAL: 50,
                    QuotaType.OBC: 25,
                    QuotaType.SC: 12,
                    QuotaType.ST: 6,
                    QuotaType.MANAGEMENT: 8,
                    QuotaType.NRI: 4,
                }
            },
            "EEE": {
                "name": "Electrical and Electronics Engineering",
                "seats": {
                    QuotaType.GENERAL: 40,
                    QuotaType.OBC: 20,
                    QuotaType.SC: 10,
                    QuotaType.ST: 5,
                    QuotaType.MANAGEMENT: 6,
                    QuotaType.NRI: 3,
                }
            },
            "ME": {
                "name": "Mechanical Engineering",
                "seats": {
                    QuotaType.GENERAL: 45,
                    QuotaType.OBC: 22,
                    QuotaType.SC: 11,
                    QuotaType.ST: 5,
                    QuotaType.MANAGEMENT: 7,
                    QuotaType.NRI: 3,
                }
            },
            "CE": {
                "name": "Civil Engineering",
                "seats": {
                    QuotaType.GENERAL: 30,
                    QuotaType.OBC: 15,
                    QuotaType.SC: 8,
                    QuotaType.ST: 4,
                    QuotaType.MANAGEMENT: 5,
                    QuotaType.NRI: 2,
                }
            },
            "IT": {
                "name": "Information Technology",
                "seats": {
                    QuotaType.GENERAL: 35,
                    QuotaType.OBC: 18,
                    QuotaType.SC: 9,
                    QuotaType.ST: 4,
                    QuotaType.MANAGEMENT: 6,
                    QuotaType.NRI: 3,
                }
            },
        }

        # 3. Create Branches and Seat Matrix entries
        for code, data in branches_data.items():
            branch, created = Branch.objects.update_or_create(
                code=code,
                defaults={"name": data["name"], "is_active": True}
            )
            if created:
                self.stdout.write(f"Created Branch: {code}")
            
            for quota, count in data["seats"].items():
                sm, sm_created = SeatMatrix.objects.update_or_create(
                    branch=branch,
                    academic_year=ay,
                    quota=quota,
                    defaults={"total_seats": count}
                )
                if sm_created:
                    self.stdout.write(f"  - Created Seat Matrix for {code} - {quota}: {count}")
                else:
                    self.stdout.write(f"  - Updated Seat Matrix for {code} - {quota}: {count}")

        self.stdout.write(self.style.SUCCESS("Success: Seed Data Applied Successfully!"))
