from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Changes contact_phone from default='' (non-nullable temp default) to
    null=True, blank=True so the field is genuinely optional at the DB level.
    """

    dependencies = [
        ('agents', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agentprofile',
            name='contact_phone',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]
