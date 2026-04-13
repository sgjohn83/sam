from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0003_fieldverification_is_superseded'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
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
            field=models.UUIDField(db_index=True),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='entity_type',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='application',
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='field_name',
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='new_value',
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='old_value',
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='timestamp',
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='user',
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='user_agent',
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['entity_type', 'entity_id', '-created_at'], name='verification_entity_type_id_created_idx'),
        ),
    ]