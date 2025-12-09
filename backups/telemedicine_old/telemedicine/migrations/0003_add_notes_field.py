# Generated manually to add notes field for backward compatibility

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telemedicine', '0002_alter_telemeddocument_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='telemedicineconsultation',
            name='notes',
            field=models.TextField(
                blank=True,
                verbose_name='Notes',
                help_text='General notes about the consultation'
            ),
        ),
    ]