import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AgentProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('agency_name', models.CharField(blank=True, max_length=300, null=True)),
                ('contact_phone', models.CharField(default='', max_length=15)),
                ('address', models.JSONField(blank=True, null=True)),
                ('pan_number', models.CharField(blank=True, max_length=10, null=True)),
                ('bank_account_name', models.CharField(blank=True, max_length=200, null=True)),
                ('bank_account_number', models.CharField(blank=True, max_length=30, null=True)),
                ('bank_ifsc', models.CharField(blank=True, max_length=11, null=True)),
                ('commission_rate', models.DecimalField(decimal_places=2, default=5.0, help_text='Percentage of fee amount', max_digits=5)),
                ('is_verified', models.BooleanField(default=False)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('total_students_referred', models.IntegerField(default=0)),
                ('total_commission_earned', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(limit_choices_to={'role': 'agent'}, on_delete=django.db.models.deletion.CASCADE, related_name='agent_profile', to=settings.AUTH_USER_MODEL)),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_agents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['is_verified', 'is_active'], name='agents_agen_is_veri_1bca9d_idx'),
                ],
            },
        ),
    ]
