from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Appointment
# Using default admin site

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date', 'time', 'status', 'is_telemedicine')
    list_filter = ('status', 'date', 'doctor', 'is_telemedicine')
    search_fields = ('patient__username', 'patient__first_name', 'patient__last_name',
                    'doctor__username', 'doctor__first_name', 'doctor__last_name', 'jitsi_room_name')
    date_hierarchy = 'date'
    fieldsets = (
        (None, {
            'fields': ('patient', 'doctor')
        }),
        (_('Appointment Information'), {
            'fields': ('date', 'time', 'description', 'status')
        }),
        (_('Telemedicine Settings'), {
            'fields': ('is_telemedicine', 'jitsi_room_name'),
            'classes': ('collapse',),
        }),
    )

# Register with custom admin site
admin.site.register(Appointment, AppointmentAdmin)

# Admin registrations for doctor availability systems
try:
    from .models_availability import DoctorAvailability, DoctorTimeOff

    class DoctorAvailabilityAdmin(admin.ModelAdmin):
        list_display = ('doctor', 'get_weekday_name', 'start_time', 'end_time', 'is_active')
        list_filter = ('weekday', 'is_active', 'doctor')
        search_fields = ('doctor__username', 'doctor__first_name', 'doctor__last_name')

    class DoctorTimeOffAdmin(admin.ModelAdmin):
        list_display = ('doctor', 'start_date', 'end_date', 'is_full_day', 'reason')
        list_filter = ('is_full_day', 'start_date', 'doctor')
        search_fields = ('doctor__username', 'doctor__first_name', 'doctor__last_name', 'reason')
        date_hierarchy = 'start_date'

    # Register with custom admin site
    admin.site.register(DoctorAvailability, DoctorAvailabilityAdmin)
    admin.site.register(DoctorTimeOff, DoctorTimeOffAdmin)
except ImportError:
    pass
