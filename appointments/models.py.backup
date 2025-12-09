from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Appointment(models.Model):
    """
    Appointment model representing appointments between patients and doctors.
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

# Imports for doctor availability system
from .models_availability import DoctorAvailability, DoctorTimeOff
