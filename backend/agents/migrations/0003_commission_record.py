import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0002_contact_phone_null'),
        ('admissions', '0001_initial'),
        ('students', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CommissionRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fee_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('commission_rate', models.DecimalField(decimal_places=2, max_digits=5)),
                ('commission_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('paid', 'Paid'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('payment_reference', models.CharField(blank=True, max_length=100, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commissions', to='agents.agentprofile')),
                ('application', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='commission', to='admissions.application')),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_commissions', to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commission_records', to='students.studentprofile')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['agent', 'status'], name='agents_comm_agent_i_15080b_idx'),
                    models.Index(fields=['status', '-created_at'], name='agents_comm_status_f30f7b_idx'),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name='commissionrecord',
            constraint=models.CheckConstraint(check=models.Q(('commission_amount__gte', 0)), name='commission_amount_gte_zero'),
        ),
    ]
