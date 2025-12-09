"""
Patient Admission, Discharge, Transfer (ADT) Models for Laso Healthcare
Handles inpatient and outpatient workflow management
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta


class PatientAdmission(models.Model):
    """
    Patient admission record for inpatient stays
    """
    ADMISSION_TYPE_CHOICES = [
        ('emergency', _('Emergency Admission')),
        ('elective', _('Elective/Planned Admission')),
        ('transfer', _('Transfer from Another Facility')),
        ('maternity', _('Maternity Admission')),
        ('observation', _('Observation (Short Stay)')),
    ]
    
    STATUS_CHOICES = [
        ('admitted', _('Admitted')),
        ('in_treatment', _('In Treatment')),
        ('pending_discharge', _('Pending Discharge')),
        ('discharged', _('Discharged')),
        ('transferred', _('Transferred')),
        ('deceased', _('Deceased')),
        ('absconded', _('Left Against Medical Advice')),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('insurance', _('Insurance')),
        ('self_pay', _('Self Pay')),
        ('government', _('Government/Public')),
        ('corporate', _('Corporate')),
        ('charity', _('Charity/Free')),
    ]
    
    # Admission identification
    admission_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Admission Number')
    )
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admissions',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    
    # Admission details
    admission_type = models.CharField(
        max_length=20,
        choices=ADMISSION_TYPE_CHOICES,
        default='elective',
        verbose_name=_('Admission Type')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='admitted',
        verbose_name=_('Status')
    )
    
    # Dates and times
    admission_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Admission Date & Time')
    )
    
    expected_discharge_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Expected Discharge Date')
    )
    
    actual_discharge_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Actual Discharge Date & Time')
    )
    
    # Medical information
    admitting_doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admitted_patients',
        verbose_name=_('Admitting Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    
    attending_doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attending_patients',
        verbose_name=_('Attending Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    
    admission_diagnosis = models.TextField(
        verbose_name=_('Admission Diagnosis')
    )
    
    chief_complaint = models.TextField(
        blank=True,
        verbose_name=_('Chief Complaint')
    )
    
    # Bed assignment
    bed = models.ForeignKey(
        'core.Bed',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patient_admissions',
        verbose_name=_('Assigned Bed')
    )
    
    # Emergency contact
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Emergency Contact Name')
    )
    
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Emergency Contact Phone')
    )
    
    emergency_contact_relationship = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Relationship to Patient')
    )
    
    # Payment information
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='self_pay',
        verbose_name=_('Payment Type')
    )
    
    insurance_policy_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Insurance Policy Number')
    )
    
    # Discharge information
    discharge_diagnosis = models.TextField(
        blank=True,
        verbose_name=_('Discharge Diagnosis')
    )
    
    discharge_summary = models.TextField(
        blank=True,
        verbose_name=_('Discharge Summary')
    )
    
    discharge_instructions = models.TextField(
        blank=True,
        verbose_name=_('Discharge Instructions')
    )
    
    follow_up_instructions = models.TextField(
        blank=True,
        verbose_name=_('Follow-up Instructions')
    )
    
    discharged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discharged_patients',
        verbose_name=_('Discharged By'),
        limit_choices_to={'user_type': 'doctor'}
    )
    
    # Metadata
    notes = models.TextField(
        blank=True,
        verbose_name=_('Additional Notes')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('Patient Admission')
        verbose_name_plural = _('Patient Admissions')
        ordering = ['-admission_date']
    
    def __str__(self):
        return f"{self.admission_number} - {self.patient.get_full_name()} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-generate admission number if not provided
        if not self.admission_number:
            today = timezone.now().strftime('%Y%m%d')
            count = PatientAdmission.objects.filter(
                admission_date__date=timezone.now().date()
            ).count() + 1
            self.admission_number = f"ADM-{today}-{count:04d}"
        super().save(*args, **kwargs)
    
    @property
    def length_of_stay(self):
        """Calculate length of stay in days"""
        end_date = self.actual_discharge_date or timezone.now()
        delta = end_date - self.admission_date
        return delta.days
    
    @property
    def is_active(self):
        """Check if admission is currently active"""
        return self.status in ['admitted', 'in_treatment', 'pending_discharge']
    
    def discharge(self, discharged_by, diagnosis, summary, instructions):
        """Process patient discharge"""
        from .models_bed_management import Bed
        
        self.status = 'discharged'
        self.actual_discharge_date = timezone.now()
        self.discharged_by = discharged_by
        self.discharge_diagnosis = diagnosis
        self.discharge_summary = summary
        self.discharge_instructions = instructions
        
        # Free up the bed
        if self.bed:
            self.bed.mark_available()
        
        self.save()
    
    def transfer_bed(self, new_bed):
        """Transfer patient to a new bed"""
        old_bed = self.bed
        if old_bed:
            old_bed.mark_available()
        
        new_bed.mark_occupied(self.patient)
        self.bed = new_bed
        self.save()
        
        # Create transfer record
        PatientTransfer.objects.create(
            admission=self,
            from_bed=old_bed,
            to_bed=new_bed,
            transfer_reason='bed_transfer'
        )


class PatientTransfer(models.Model):
    """
    Record of patient transfers between beds/wards
    """
    TRANSFER_REASON_CHOICES = [
        ('bed_transfer', _('Bed/Room Transfer')),
        ('ward_transfer', _('Ward Transfer')),
        ('icu_upgrade', _('ICU Upgrade')),
        ('icu_downgrade', _('ICU Downgrade')),
        ('facility_transfer', _('External Facility Transfer')),
        ('patient_request', _('Patient Request')),
        ('medical_necessity', _('Medical Necessity')),
    ]
    
    admission = models.ForeignKey(
        PatientAdmission,
        on_delete=models.CASCADE,
        related_name='transfers',
        verbose_name=_('Admission')
    )
    
    from_bed = models.ForeignKey(
        'core.Bed',
        on_delete=models.SET_NULL,
        null=True,
        related_name='transfers_from',
        verbose_name=_('From Bed')
    )
    
    to_bed = models.ForeignKey(
        'core.Bed',
        on_delete=models.SET_NULL,
        null=True,
        related_name='transfers_to',
        verbose_name=_('To Bed')
    )
    
    transfer_reason = models.CharField(
        max_length=30,
        choices=TRANSFER_REASON_CHOICES,
        verbose_name=_('Transfer Reason')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Transfer Notes')
    )
    
    transferred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Transferred By')
    )
    
    transfer_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Transfer Date & Time')
    )
    
    class Meta:
        verbose_name = _('Patient Transfer')
        verbose_name_plural = _('Patient Transfers')
        ordering = ['-transfer_date']
    
    def __str__(self):
        return f"{self.admission.patient.get_full_name()} - {self.get_transfer_reason_display()}"


class VisitType(models.Model):
    """
    Define different visit types for classification
    """
    CATEGORY_CHOICES = [
        ('outpatient', _('Outpatient')),
        ('inpatient', _('Inpatient')),
        ('emergency', _('Emergency')),
        ('day_surgery', _('Day Surgery')),
        ('telemedicine', _('Telemedicine')),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('Visit Type Name')
    )
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='outpatient',
        verbose_name=_('Category')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    default_duration_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name=_('Default Duration (minutes)')
    )
    
    requires_admission = models.BooleanField(
        default=False,
        verbose_name=_('Requires Admission')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    
    class Meta:
        verbose_name = _('Visit Type')
        verbose_name_plural = _('Visit Types')
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
