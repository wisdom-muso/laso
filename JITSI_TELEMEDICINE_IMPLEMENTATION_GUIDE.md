# Jitsi Meet Telemedicine Integration Guide

This guide provides step-by-step instructions to extend your existing Django healthcare system with Jitsi Meet telemedicine functionality.

## Overview

The integration adds:
- **Time-based access control**: Video calls available 10 minutes before to 30 minutes after appointment
- **UUID-based room names**: Secure, unique room identifiers
- **Bootstrap responsive UI**: Professional telemedicine interface
- **Jitsi External API**: Full-featured video conferencing
- **Doctor/Patient verification**: Only authorized users can join calls

## Implementation Steps

### 1. Update Appointment Model

Replace your existing `appointments/models.py` with the updated version:

```bash
# Backup current model
cp appointments/models.py appointments/models.py.backup

# Replace with updated model
cp appointments/models_updated.py appointments/models.py
```

### 2. Create and Run Migration

```bash
# Create migration for new fields
python manage.py makemigrations appointments

# Apply migration
python manage.py migrate appointments
```

Or manually create migration file:
```bash
# Check latest migration number
ls appointments/migrations/

# Create new migration file (replace XXXX with next number)
# Copy content from create_jitsi_migration.py
```

### 3. Update Django Settings

Add to your `laso/settings.py`:

```python
# Jitsi Meet Configuration
JITSI_DOMAIN = "meet.jit.si"  # Can be changed to self-hosted domain later

# Updated Telemedicine Settings with Jitsi integration
TELEMEDICINE_SETTINGS = {
    'MAX_SESSION_DURATION': 120,  # minutes
    'DEFAULT_SESSION_DURATION': 30,  # minutes
    'WEBRTC_STUN_SERVERS': [
        'stun:stun.l.google.com:19302',
        'stun:stun1.l.google.com:19302',
    ],
    'RECORDING_ENABLED': True,
    'RECORDING_PATH': MEDIA_ROOT + '/recordings/',
    'AUTO_END_SESSION_AFTER': 150,  # minutes
    'JITSI_DOMAIN': JITSI_DOMAIN,
    'CALL_WINDOW_BEFORE': 10,  # minutes before appointment
    'CALL_WINDOW_AFTER': 30,   # minutes after appointment
    'ENABLE_JITSI_INTEGRATION': True,
}
```

### 4. Add Jitsi Views

Copy the Jitsi views to your telemedicine app:

```bash
# Add Jitsi views to telemedicine app
cp telemedicine/views_jitsi.py telemedicine/views_jitsi.py

# Or append to existing views.py
cat telemedicine/views_jitsi.py >> telemedicine/views.py
```

### 5. Update URL Configuration

Add Jitsi URLs to your `telemedicine/urls.py`:

```python
# Add these imports
from . import views_jitsi

# Add these URL patterns to your existing urlpatterns
urlpatterns += [
    # Jitsi Meet Integration URLs
    path('jitsi/<int:appointment_id>/', views_jitsi.jitsi_telemedicine_room, name='jitsi-room'),
    path('appointment/<int:appointment_id>/toggle-telemedicine/', views_jitsi.toggle_telemedicine, name='toggle-telemedicine'),
    path('appointment/<int:appointment_id>/check-status/', views_jitsi.check_telemedicine_status, name='check-telemedicine-status'),
    path('appointment/<int:appointment_id>/detail/', views_jitsi.appointment_detail_with_telemedicine, name='appointment-detail-telemedicine'),
]
```

### 6. Add Templates

Copy the template files to your templates directory:

```bash
# Ensure template directories exist
mkdir -p templates/telemedicine
mkdir -p templates/appointments

# Copy Jitsi room template
cp templates/telemedicine/jitsi_room.html templates/telemedicine/

# Copy enhanced appointment detail template
cp templates/appointments/appointment_detail_telemedicine.html templates/appointments/
```

### 7. Update Admin Interface (Optional)

Add Jitsi fields to your admin interface in `appointments/admin.py`:

```python
from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'date', 'time', 'status', 'is_telemedicine']
    list_filter = ['status', 'is_telemedicine', 'date']
    search_fields = ['patient__username', 'doctor__username']
    readonly_fields = ['jitsi_room_name', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'doctor', 'date', 'time', 'description', 'status')
        }),
        ('Telemedicine', {
            'fields': ('is_telemedicine', 'jitsi_room_name'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
```

## Usage Instructions

### For Doctors

1. **Enable Telemedicine**: In appointment details, toggle the telemedicine switch
2. **Join Video Call**: Click "Join Video Call" when available (10 min before appointment)
3. **Manage Settings**: Use the toggle to enable/disable telemedicine per appointment

### For Patients

1. **Access Appointment**: Navigate to appointment details from dashboard
2. **Wait for Availability**: System shows countdown until call window opens
3. **Join Call**: Click "Join Video Call" when available
4. **Auto-refresh**: Page automatically refreshes when call becomes available

### Time Windows

- **Before Appointment**: Call available 10 minutes before scheduled time
- **After Appointment**: Call remains available for 30 minutes after scheduled time
- **Outside Window**: System shows appropriate waiting message with countdown

## Security Features

### Room Security
- **UUID-based room names**: Each appointment gets unique, unpredictable room identifier
- **User verification**: Only assigned doctor and patient can join calls
- **Time-based access**: Calls only available within defined time windows

### Privacy Protection
- **No recording by default**: Jitsi recording disabled in interface config
- **Secure domain**: Uses HTTPS-only Jitsi Meet public instance
- **Session isolation**: Each appointment has separate, private room

## Customization Options

### Jitsi Configuration

Modify `jitsi_config` in views to customize:

```python
'configOverwrite': {
    'startWithAudioMuted': True,  # Start muted
    'startWithVideoMuted': False, # Start with video
    'enableWelcomePage': False,   # Skip welcome
    'prejoinPageEnabled': True,   # Enable prejoin
    'disableInviteFunctions': True, # Disable invites
},
```

### Time Windows

Adjust in settings:

```python
TELEMEDICINE_SETTINGS = {
    'CALL_WINDOW_BEFORE': 15,  # 15 minutes before
    'CALL_WINDOW_AFTER': 45,   # 45 minutes after
}
```

### Self-hosted Jitsi

To use your own Jitsi server:

```python
JITSI_DOMAIN = "your-jitsi-domain.com"
```

## Testing

### Test Scenarios

1. **Time-based Access**:
   - Try joining before 10-minute window
   - Join during valid window
   - Try joining after 30-minute window

2. **User Authorization**:
   - Doctor accessing their appointment
   - Patient accessing their appointment
   - Unauthorized user attempting access

3. **Room Generation**:
   - Verify unique room names
   - Test room persistence across sessions

### Test Commands

```bash
# Run Django tests
python manage.py test appointments
python manage.py test telemedicine

# Check migrations
python manage.py showmigrations

# Verify models
python manage.py shell
>>> from appointments.models import Appointment
>>> apt = Appointment.objects.first()
>>> apt.get_jitsi_room_name()
>>> apt.is_available_for_call()
```

## Troubleshooting

### Common Issues

1. **Migration Errors**:
   ```bash
   python manage.py migrate --fake appointments XXXX
   python manage.py migrate appointments
   ```

2. **Template Not Found**:
   - Verify template paths in TEMPLATES setting
   - Check template file locations

3. **URL Errors**:
   - Ensure URL names match template references
   - Check URL namespace configuration

4. **Jitsi Not Loading**:
   - Verify HTTPS connection
   - Check browser console for errors
   - Ensure external_api.js loads correctly

### Debug Mode

Enable debug logging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'telemedicine.log',
        },
    },
    'loggers': {
        'telemedicine': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Production Considerations

### Performance
- Consider CDN for Jitsi External API
- Implement caching for appointment queries
- Use database indexing on telemedicine fields

### Security
- Implement rate limiting on telemedicine endpoints
- Add CSRF protection to all POST requests
- Consider additional authentication for sensitive operations

### Monitoring
- Log telemedicine session starts/ends
- Monitor room creation and usage
- Track user access patterns

## Support

For technical issues:
1. Check Django logs for errors
2. Verify Jitsi Meet connectivity
3. Test with different browsers
4. Review network connectivity

## Next Steps

1. **Test the integration** with sample appointments
2. **Train users** on the new telemedicine features
3. **Monitor usage** and gather feedback
4. **Consider enhancements** like recording, chat integration, or mobile optimization

---

**Implementation Complete!** Your Django healthcare system now supports secure, time-controlled video consultations using Jitsi Meet.
