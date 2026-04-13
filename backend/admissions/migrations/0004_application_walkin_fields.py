from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('admissions', '0003_seed_locked_application'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='admission_channel',
            field=models.CharField(
                max_length=10,
                choices=[('online', 'Online'), ('walkin', 'Walk-In')],
                default='online',
            ),
        ),
        migrations.AddField(
            model_name='application',
            name='fee_deadline',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='application',
            name='payment_reference_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='application',
            name='fee_instruction_sent_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.RunSQL(
            sql="UPDATE admissions_application SET admission_channel = 'online' WHERE admission_channel IS NULL;",
            reverse_sql="",
        ),
    ]


class RollbackMigration(migrations.Migration):

    dependencies = [
        ('admissions', '0004_application_walkin_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='application',
            name='admission_channel',
        ),
        migrations.RemoveField(
            model_name='application',
            name='fee_deadline',
        ),
        migrations.RemoveField(
            model_name='application',
            name='payment_reference_id',
        ),
        migrations.RemoveField(
            model_name='application',
            name='fee_instruction_sent_at',
        ),
    ]
