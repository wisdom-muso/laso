"""
SOAP Notes Clinical Documentation Models for Laso Healthcare
Implements structured clinical documentation following SOAP format:
- Subjective: Patient's symptoms and history
- Objective: Observable/measurable findings
- Assessment: Diagnosis and clinical impressions
- Plan: Treatment plan and follow-up
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from appointments.models import Appointment


class SOAPNote(models.Model):
    """
    SOAP Note for structured clinical documentation
    """
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('completed', _('Completed')),
        ('amended', _('Amended')),
        ('signed', _('Signed & Locked')),
    ]
    
    ENCOUNTER_TYPE_CHOICES = [
        ('initial', _('Initial Visit')),
        ('follow_up', _('Follow-up Visit')),
        ('urgent', _('Urgent/Walk-in')),
        ('emergency', _('Emergency')),
        ('consultation', _('Consultation')),
        ('telemedicine', _('Telemedicine')),
        ('inpatient_round', _('Inpatient Rounding')),
        ('discharge', _('Discharge Note')),
    ]
    
    # Relationships
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='soap_notes',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authored_soap_notes',
        verbose_name=_('Provider/Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='soap_notes',
        verbose_name=_('Related Appointment')
    )
    
    admission = models.ForeignKey(
        'core.PatientAdmission',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='soap_notes',
        verbose_name=_('Related Admission')
    )
    
    # Note metadata
    encounter_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Encounter Date & Time')
    )
    
    encounter_type = models.CharField(
        max_length=20,
        choices=ENCOUNTER_TYPE_CHOICES,
        default='follow_up',
        verbose_name=_('Encounter Type')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Status')
    )
    
    # Chief Complaint (reason for visit)
    chief_complaint = models.TextField(
        verbose_name=_('Chief Complaint'),
        help_text=_('Primary reason for the visit in patient\'s words')
    )
    
    # ===================
    # SUBJECTIVE Section
    # ===================
    # What the patient reports
    
    history_of_present_illness = models.TextField(
        verbose_name=_('History of Present Illness (HPI)'),
        help_text=_('Detailed description of current symptoms, onset, duration, severity')
    )
    
    symptom_onset = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Symptom Onset'),
        help_text=_('When did symptoms begin?')
    )
    
    symptom_duration = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Symptom Duration')
    )
    
    symptom_severity = models.CharField(
        max_length=20,
        choices=[
            ('mild', _('Mild')),
            ('moderate', _('Moderate')),
            ('severe', _('Severe')),
        ],
        blank=True,
        verbose_name=_('Symptom Severity')
    )
    
    aggravating_factors = models.TextField(
        blank=True,
        verbose_name=_('Aggravating Factors'),
        help_text=_('What makes symptoms worse?')
    )
    
    alleviating_factors = models.TextField(
        blank=True,
        verbose_name=_('Alleviating Factors'),
        help_text=_('What makes symptoms better?')
    )
    
    past_medical_history = models.TextField(
        blank=True,
        verbose_name=_('Past Medical History')
    )
    
    medications_at_home = models.TextField(
        blank=True,
        verbose_name=_('Current Medications'),
        help_text=_('List of medications patient is currently taking')
    )
    
    allergies = models.TextField(
        blank=True,
        verbose_name=_('Allergies')
    )
    
    family_history = models.TextField(
        blank=True,
        verbose_name=_('Family History')
    )
    
    social_history = models.TextField(
        blank=True,
        verbose_name=_('Social History'),
        help_text=_('Smoking, alcohol, occupation, living situation')
    )
    
    review_of_systems = models.TextField(
        blank=True,
        verbose_name=_('Review of Systems (ROS)'),
        help_text=_('Systematic review of body systems')
    )
    
    # ===================
    # OBJECTIVE Section
    # ===================
    # What the provider observes/measures
    
    vital_signs_summary = models.TextField(
        blank=True,
        verbose_name=_('Vital Signs'),
        help_text=_('BP, HR, RR, Temp, O2 Sat, Weight, Height')
    )
    
    general_appearance = models.TextField(
        blank=True,
        verbose_name=_('General Appearance'),
        help_text=_('Patient\'s overall appearance and demeanor')
    )
    
    physical_examination = models.TextField(
        verbose_name=_('Physical Examination Findings'),
        help_text=_('Detailed findings from physical exam')
    )
    
    # System-specific exam findings
    heent_exam = models.TextField(
        blank=True,
        verbose_name=_('HEENT Exam'),
        help_text=_('Head, Eyes, Ears, Nose, Throat')
    )
    
    cardiovascular_exam = models.TextField(
        blank=True,
        verbose_name=_('Cardiovascular Exam')
    )
    
    respiratory_exam = models.TextField(
        blank=True,
        verbose_name=_('Respiratory Exam')
    )
    
    abdominal_exam = models.TextField(
        blank=True,
        verbose_name=_('Abdominal Exam')
    )
    
    neurological_exam = models.TextField(
        blank=True,
        verbose_name=_('Neurological Exam')
    )
    
    musculoskeletal_exam = models.TextField(
        blank=True,
        verbose_name=_('Musculoskeletal Exam')
    )
    
    skin_exam = models.TextField(
        blank=True,
        verbose_name=_('Skin/Integumentary Exam')
    )
    
    psychiatric_exam = models.TextField(
        blank=True,
        verbose_name=_('Psychiatric/Mental Status Exam')
    )
    
    lab_results = models.TextField(
        blank=True,
        verbose_name=_('Laboratory Results'),
        help_text=_('Relevant lab findings')
    )
    
    imaging_results = models.TextField(
        blank=True,
        verbose_name=_('Imaging Results'),
        help_text=_('X-ray, CT, MRI, Ultrasound findings')
    )
    
    other_diagnostic_results = models.TextField(
        blank=True,
        verbose_name=_('Other Diagnostic Results'),
        help_text=_('EKG, spirometry, other tests')
    )
    
    # ===================
    # ASSESSMENT Section
    # ===================
    # Provider's clinical impressions
    
    primary_diagnosis = models.CharField(
        max_length=255,
        verbose_name=_('Primary Diagnosis')
    )
    
    primary_diagnosis_icd10 = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Primary Diagnosis ICD-10 Code')
    )
    
    secondary_diagnoses = models.TextField(
        blank=True,
        verbose_name=_('Secondary/Additional Diagnoses'),
        help_text=_('List additional diagnoses, one per line')
    )
    
    differential_diagnoses = models.TextField(
        blank=True,
        verbose_name=_('Differential Diagnoses'),
        help_text=_('Other conditions being considered')
    )
    
    clinical_impression = models.TextField(
        blank=True,
        verbose_name=_('Clinical Impression'),
        help_text=_('Overall assessment and reasoning')
    )
    
    prognosis = models.CharField(
        max_length=20,
        choices=[
            ('excellent', _('Excellent')),
            ('good', _('Good')),
            ('fair', _('Fair')),
            ('guarded', _('Guarded')),
            ('poor', _('Poor')),
        ],
        blank=True,
        verbose_name=_('Prognosis')
    )
    
    # ===================
    # PLAN Section
    # ===================
    # Treatment plan and next steps
    
    treatment_plan = models.TextField(
        verbose_name=_('Treatment Plan'),
        help_text=_('Detailed treatment plan')
    )
    
    medications_prescribed = models.TextField(
        blank=True,
        verbose_name=_('Medications Prescribed'),
        help_text=_('New prescriptions or changes to medications')
    )
    
    procedures_performed = models.TextField(
        blank=True,
        verbose_name=_('Procedures Performed'),
        help_text=_('Any procedures done during this visit')
    )
    
    procedures_ordered = models.TextField(
        blank=True,
        verbose_name=_('Procedures Ordered'),
        help_text=_('Procedures scheduled for future')
    )
    
    labs_ordered = models.TextField(
        blank=True,
        verbose_name=_('Labs Ordered')
    )
    
    imaging_ordered = models.TextField(
        blank=True,
        verbose_name=_('Imaging Ordered')
    )
    
    referrals = models.TextField(
        blank=True,
        verbose_name=_('Referrals'),
        help_text=_('Specialist referrals')
    )
    
    patient_education = models.TextField(
        blank=True,
        verbose_name=_('Patient Education'),
        help_text=_('Education provided to patient')
    )
    
    lifestyle_modifications = models.TextField(
        blank=True,
        verbose_name=_('Lifestyle Modifications'),
        help_text=_('Diet, exercise, behavior changes recommended')
    )
    
    follow_up_instructions = models.TextField(
        blank=True,
        verbose_name=_('Follow-up Instructions')
    )
    
    follow_up_timeframe = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Follow-up Timeframe'),
        help_text=_('e.g., "2 weeks", "1 month", "as needed"')
    )
    
    return_precautions = models.TextField(
        blank=True,
        verbose_name=_('Return Precautions'),
        help_text=_('When patient should return immediately')
    )
    
    # ===================
    # Metadata
    # ===================
    
    time_spent_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Time Spent (minutes)'),
        help_text=_('Total time spent with patient')
    )
    
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Signed At')
    )
    
    co_signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cosigned_soap_notes',
        verbose_name=_('Co-signed By')
    )
    
    amendment_notes = models.TextField(
        blank=True,
        verbose_name=_('Amendment Notes'),
        help_text=_('Notes about any amendments made after signing')
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
        verbose_name = _('SOAP Note')
        verbose_name_plural = _('SOAP Notes')
        ordering = ['-encounter_date']
    
    def __str__(self):
        return f"SOAP Note - {self.patient.get_full_name()} - {self.encounter_date.strftime('%Y-%m-%d')}"
    
    def sign_note(self):
        """Sign and lock the note"""
        self.status = 'signed'
        self.signed_at = timezone.now()
        self.save()
    
    def amend_note(self, amendment_text):
        """Add amendment to signed note"""
        if self.status == 'signed':
            self.status = 'amended'
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
            self.amendment_notes = f"{self.amendment_notes}\n\n[Amendment {timestamp}]\n{amendment_text}".strip()
            self.save()
    
    @property
    def is_locked(self):
        """Check if note is locked for editing"""
        return self.status in ['signed', 'amended']
    
    def get_soap_summary(self):
        """Get a brief summary of SOAP note"""
        return {
            'subjective': self.chief_complaint[:100] + '...' if len(self.chief_complaint) > 100 else self.chief_complaint,
            'objective': self.vital_signs_summary[:100] if self.vital_signs_summary else 'No vitals recorded',
            'assessment': self.primary_diagnosis,
            'plan': self.treatment_plan[:100] + '...' if len(self.treatment_plan) > 100 else self.treatment_plan
        }
