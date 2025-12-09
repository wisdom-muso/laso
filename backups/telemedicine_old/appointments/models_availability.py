from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import datetime

class DoctorAvailability(models.Model):
    """
    Doctor availability calendar. Determines which days and times 
    doctors are available.
    """
    WEEKDAY_CHOICES = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]
    
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availabilities',
        verbose_name=_('Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    weekday = models.IntegerField(
        choices=WEEKDAY_CHOICES,
        verbose_name=_('Day of Week')
    )
    start_time = models.TimeField(
        verbose_name=_('Start Time')
    )
    end_time = models.TimeField(
        verbose_name=_('End Time')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active?')
    )
    
    class Meta:
        verbose_name = _('Doctor Availability')
        verbose_name_plural = _('Doctor Availabilities')
        ordering = ['weekday', 'start_time']
        unique_together = ['doctor', 'weekday', 'start_time', 'end_time']
    
    def __str__(self):
        return f"{self.doctor} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"
    
    def get_weekday_name(self):
        return self.get_weekday_display()
    
    def is_available_on_date(self, date):
        """Checks if the doctor is available on a specific date"""
        # Does the date match this availability's day?
        return date.weekday() == self.weekday and self.is_active

class DoctorTimeOff(models.Model):
    """
    Doctor time off days/hours. Specifies times when they are on leave
    for special reasons during their normally available times.
    """
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='time_offs',
        verbose_name=_('Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    start_date = models.DateField(
        verbose_name=_('Start Date')
    )
    end_date = models.DateField(
        verbose_name=_('End Date')
    )
    start_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name=_('Start Time'),
        help_text=_('If not full day leave')
    )
    end_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name=_('End Time'),
        help_text=_('If not full day leave')
    )
    reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Reason for Leave')
    )
    is_full_day = models.BooleanField(
        default=True,
        verbose_name=_('Full Day?')
    )
    
    class Meta:
        verbose_name = _('Doctor Time Off')
        verbose_name_plural = _('Doctor Time Offs')
        ordering = ['-start_date', '-start_time']
    
    def __str__(self):
        if self.is_full_day:
            return f"{self.doctor} - {self.start_date} - {self.end_date}"
        return f"{self.doctor} - {self.start_date} {self.start_time} - {self.end_date} {self.end_time}"
