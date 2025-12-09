from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

class Appointment(models.Model):
    """
    Appointment model representing appointments between patients and doctors.
    Extended with Jitsi Meet telemedicine functionality.
    """
    STATUS_CHOICES = [
        ('planned', _('Planned')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_appointments',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_appointments',
        verbose_name=_('Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    date = models.DateField(
        verbose_name=_('Date')
    )
    time = models.TimeField(
        verbose_name=_('Time')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned',
        verbose_name=_('Status')
    )
    
    # Jitsi Meet Integration Fields
    jitsi_room_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Jitsi Room Name'),
        help_text=_('Unique room name for video consultation')
    )
    is_telemedicine = models.BooleanField(
        default=False,
        verbose_name=_('Telemedicine Appointment'),
        help_text=_('Enable video consultation for this appointment')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created Date')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated Date')
    )

    class Meta:
        verbose_name = _('Appointment')
        verbose_name_plural = _('Appointments')
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.patient} - {self.doctor} - {self.date} {self.time}"

    def get_jitsi_room_name(self):
        """
        Generate or return existing Jitsi room name for this appointment
        """
        if not self.jitsi_room_name:
            # Generate UUID-based room name for privacy
            room_uuid = str(uuid.uuid4()).replace('-', '')[:12]
            self.jitsi_room_name = f"telemed_{room_uuid}"
            self.save(update_fields=['jitsi_room_name'])
        return self.jitsi_room_name

    def is_available_for_call(self):
        """
        Check if telemedicine call is available for this appointment
        Available 10 minutes before and up to 30 minutes after scheduled time
        """
        if not self.is_telemedicine:
            return False, "This is not a telemedicine appointment"
        
        now = timezone.now()
        appointment_datetime = timezone.make_aware(
            datetime.combine(self.date, self.time)
        )
        
        # Available 10 minutes before appointment
        start_window = appointment_datetime - timedelta(minutes=10)
        # Available up to 30 minutes after appointment
        end_window = appointment_datetime + timedelta(minutes=30)
        
        if now < start_window:
            time_until = start_window - now
            minutes_until = int(time_until.total_seconds() / 60)
            return False, f"Telemedicine not yet available. You can join in {minutes_until} minutes."
        elif now > end_window:
            return False, "Telemedicine window has expired for this appointment."
        else:
            return True, "Ready to join telemedicine consultation"

    def can_user_join_call(self, user):
        """
        Check if the given user can join this telemedicine call
        Only doctor and patient associated with appointment can join
        """
        if user == self.doctor or user == self.patient:
            return True
        return False

    def get_appointment_datetime(self):
        """
        Get appointment datetime as timezone-aware datetime object
        """
        return timezone.make_aware(datetime.combine(self.date, self.time))

    def time_until_available(self):
        """
        Get time until telemedicine becomes available
        """
        now = timezone.now()
        appointment_datetime = self.get_appointment_datetime()
        start_window = appointment_datetime - timedelta(minutes=10)
        
        if now < start_window:
            time_diff = start_window - now
            return int(time_diff.total_seconds() / 60)
        return 0

# Imports for doctor availability system
from .models_availability import DoctorAvailability, DoctorTimeOff
