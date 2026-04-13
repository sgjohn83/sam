from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0004_alter_auditlog_schema'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='auditlog',
            name='verification_entity_type_id_created_idx',
        ),
        migrations.AddField(
            model_name='auditlog',
            name='application',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='audit_logs',
                to='admissions.application'
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='field_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='new_value',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='old_value',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='auth.user'
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='user_agent',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='actor',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='audit_actions',
                to='auth.user'
            ),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='after_json',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='before_json',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='entity_id',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='entity_type',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['application', '-timestamp'], name='verification_applicat_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', '-timestamp'], name='verification_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['-timestamp'], name='verification_timest_idx'),
        ),
    ]