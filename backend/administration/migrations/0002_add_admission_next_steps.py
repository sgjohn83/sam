# Generated manually for adding configurable next-steps to AcademicYear
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='academicyear',
            name='orientation_date',
            field=models.DateField(blank=True, help_text='Date of orientation program', null=True),
        ),
        migrations.AddField(
            model_name='academicyear',
            name='orientation_venue',
            field=models.CharField(blank=True, help_text='Venue for orientation program', max_length=200),
        ),
        migrations.AddField(
            model_name='academicyear',
            name='reporting_date',
            field=models.DateField(blank=True, help_text='Date for reporting to college', null=True),
        ),
    ]