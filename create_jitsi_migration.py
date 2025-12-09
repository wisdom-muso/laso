"""
Django Migration for Jitsi Meet Integration
Run this to create the migration file for the new fields
"""

# Create migration file manually or use Django's makemigrations
migration_content = '''
# Generated migration for Jitsi Meet integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0001_initial'),  # Replace with your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='jitsi_room_name',
            field=models.CharField(blank=True, help_text='Unique room name for video consultation', max_length=100, null=True, verbose_name='Jitsi Room Name'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='is_telemedicine',
            field=models.BooleanField(default=False, help_text='Enable video consultation for this appointment', verbose_name='Telemedicine Appointment'),
        ),
    ]
'''

print("Save this as appointments/migrations/XXXX_add_jitsi_fields.py")
print("Replace XXXX with the next migration number")
print("\nMigration content:")
print(migration_content)
