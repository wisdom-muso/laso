from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class VitalSign(models.Model):
    """
    Model to store patient vital signs including blood pressure, heart rate, etc.
    Designed for hypertension management and cardiovascular risk assessment.
    """
    RISK_LEVEL_CHOICES = [
        ('low', _('Low Risk')),
        ('normal', _('Normal')),
        ('elevated', _('Elevated')),
        ('high', _('High Risk')),
        ('critical', _('Critical')),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vital_signs',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_vitals',
        verbose_name=_('Recorded By'),
        limit_choices_to={'user_type__in': ['doctor', 'admin']}
    )
    
    # Blood Pressure (Primary focus for hypertension management)
    systolic_bp = models.PositiveIntegerField(
        validators=[MinValueValidator(50), MaxValueValidator(300)],
        verbose_name=_('Systolic Blood Pressure (mmHg)'),
        help_text=_('Normal: 90-120 mmHg')
    )
    
    diastolic_bp = models.PositiveIntegerField(
        validators=[MinValueValidator(30), MaxValueValidator(200)],
        verbose_name=_('Diastolic Blood Pressure (mmHg)'),
        help_text=_('Normal: 60-80 mmHg')
    )
    
    # Heart Rate
    heart_rate = models.PositiveIntegerField(
        validators=[MinValueValidator(30), MaxValueValidator(250)],
        verbose_name=_('Heart Rate (bpm)'),
        help_text=_('Normal: 60-100 bpm')
    )
    
    # Additional Vitals
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('30.0')), MaxValueValidator(Decimal('45.0'))],
        null=True,
        blank=True,
        verbose_name=_('Body Temperature (°C)'),
        help_text=_('Normal: 36.1-37.2°C')
    )
    
    respiratory_rate = models.PositiveIntegerField(
        validators=[MinValueValidator(8), MaxValueValidator(60)],
        null=True,
        blank=True,
        verbose_name=_('Respiratory Rate (breaths/min)'),
        help_text=_('Normal: 12-20 breaths/min')
    )
    
    oxygen_saturation = models.PositiveIntegerField(
        validators=[MinValueValidator(70), MaxValueValidator(100)],
        null=True,
        blank=True,
        verbose_name=_('Oxygen Saturation (%)'),
        help_text=_('Normal: 95-100%')
    )
    
    # Weight and BMI tracking
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('20.0')), MaxValueValidator(Decimal('500.0'))],
        null=True,
        blank=True,
        verbose_name=_('Weight (kg)')
    )
    
    height = models.PositiveIntegerField(
        validators=[MinValueValidator(100), MaxValueValidator(250)],
        null=True,
        blank=True,
        verbose_name=_('Height (cm)')
    )
    
    # Lab Values (for comprehensive cardiovascular assessment)
    cholesterol_total = models.PositiveIntegerField(
        validators=[MinValueValidator(100), MaxValueValidator(500)],
        null=True,
        blank=True,
        verbose_name=_('Total Cholesterol (mg/dL)'),
        help_text=_('Normal: <200 mg/dL')
    )
    
    cholesterol_ldl = models.PositiveIntegerField(
        validators=[MinValueValidator(50), MaxValueValidator(300)],
        null=True,
        blank=True,
        verbose_name=_('LDL Cholesterol (mg/dL)'),
        help_text=_('Normal: <100 mg/dL')
    )
    
    cholesterol_hdl = models.PositiveIntegerField(
        validators=[MinValueValidator(20), MaxValueValidator(150)],
        null=True,
        blank=True,
        verbose_name=_('HDL Cholesterol (mg/dL)'),
        help_text=_('Normal: >40 mg/dL (men), >50 mg/dL (women)')
    )
    
    blood_glucose = models.PositiveIntegerField(
        validators=[MinValueValidator(50), MaxValueValidator(500)],
        null=True,
        blank=True,
        verbose_name=_('Blood Glucose (mg/dL)'),
        help_text=_('Normal fasting: 70-100 mg/dL')
    )
    
    # Risk Assessment
    cardiovascular_risk_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Cardiovascular Risk Score (%)'),
        help_text=_('10-year cardiovascular risk percentage')
    )
    
    overall_risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVEL_CHOICES,
        default='normal',
        verbose_name=_('Overall Risk Level')
    )
    
    # Notes and Context
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Clinical Notes')
    )
    
    measurement_context = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Measurement Context'),
        help_text=_('e.g., "After exercise", "Morning reading", "Post-medication"')
    )
    
    # Timestamps
    recorded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Recorded At')
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
        verbose_name = _('Vital Sign Record')
        verbose_name_plural = _('Vital Sign Records')
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['patient', '-recorded_at']),
            models.Index(fields=['overall_risk_level']),
            models.Index(fields=['recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.patient} - {self.systolic_bp}/{self.diastolic_bp} mmHg - {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def blood_pressure_display(self):
        """Return formatted blood pressure reading"""
        return f"{self.systolic_bp}/{self.diastolic_bp}"
    
    @property
    def bmi(self):
        """Calculate BMI if height and weight are available"""
        if self.height and self.weight:
            height_m = float(self.height) / 100
            return round(float(self.weight) / (height_m ** 2), 1)
        return None
    
    @property
    def bp_category(self):
        """Categorize blood pressure according to AHA guidelines"""
        if self.systolic_bp < 120 and self.diastolic_bp < 80:
            return 'normal'
        elif self.systolic_bp < 130 and self.diastolic_bp < 80:
            return 'elevated'
        elif (120 <= self.systolic_bp <= 129) and self.diastolic_bp < 80:
            return 'elevated'
        elif (130 <= self.systolic_bp <= 139) or (80 <= self.diastolic_bp <= 89):
            return 'stage1'
        elif self.systolic_bp >= 140 or self.diastolic_bp >= 90:
            return 'stage2'
        elif self.systolic_bp > 180 or self.diastolic_bp > 120:
            return 'crisis'
        return 'unknown'
    
    def get_bp_risk_level(self):
        """Get blood pressure risk level for display"""
        bp_cat = self.bp_category
        if bp_cat == 'crisis':
            return 'critical'
        elif bp_cat == 'stage2':
            return 'high'
        elif bp_cat == 'stage1':
            return 'elevated'
        elif bp_cat == 'elevated':
            return 'elevated'
        else:
            return 'normal'
    
    def calculate_risk_level(self):
        """Calculate overall risk level based on vital signs"""
        risk_factors = 0
        
        # Blood pressure risk
        bp_cat = self.bp_category
        if bp_cat in ['stage2', 'crisis']:
            risk_factors += 3
        elif bp_cat == 'stage1':
            risk_factors += 2
        elif bp_cat == 'elevated':
            risk_factors += 1
        
        # Heart rate risk
        if self.heart_rate > 100 or self.heart_rate < 60:
            risk_factors += 1
        
        # Cholesterol risk
        if self.cholesterol_total and self.cholesterol_total > 240:
            risk_factors += 2
        elif self.cholesterol_total and self.cholesterol_total > 200:
            risk_factors += 1
        
        # Blood glucose risk
        if self.blood_glucose and self.blood_glucose > 126:
            risk_factors += 2
        elif self.blood_glucose and self.blood_glucose > 100:
            risk_factors += 1
        
        # BMI risk
        bmi = self.bmi
        if bmi and bmi > 30:
            risk_factors += 2
        elif bmi and bmi > 25:
            risk_factors += 1
        
        # Determine risk level
        if risk_factors >= 6:
            return 'critical'
        elif risk_factors >= 4:
            return 'high'
        elif risk_factors >= 2:
            return 'elevated'
        elif risk_factors >= 1:
            return 'normal'
        else:
            return 'low'
    
    def get_risk_percentage(self):
        """Calculate risk percentage based on vital signs"""
        risk_level = self.calculate_risk_level()
        
        # Base percentages for each risk level
        risk_percentages = {
            'low': 15,
            'normal': 25,
            'elevated': 45,
            'high': 70,
            'critical': 90
        }
        
        base_percentage = risk_percentages.get(risk_level, 25)
        
        # Add some variation based on specific values
        variation = 0
        
        # Blood pressure variation
        if self.systolic_bp > 140:
            variation += 10
        elif self.systolic_bp > 130:
            variation += 5
        
        # Heart rate variation
        if self.heart_rate > 100:
            variation += 5
        elif self.heart_rate < 60:
            variation += 3
        
        # Cholesterol variation
        if self.cholesterol_total and self.cholesterol_total > 240:
            variation += 8
        elif self.cholesterol_total and self.cholesterol_total > 200:
            variation += 3
        
        final_percentage = min(95, base_percentage + variation)
        return final_percentage
    
    def get_health_assessment_message(self):
        """Get detailed health assessment message based on vitals"""
        risk_level = self.calculate_risk_level()
        
        messages = {
            'low': "Your blood pressure and cholesterol levels are within normal range. Continue with your current lifestyle and medication.",
            'normal': "Your vital signs are generally good. Consider maintaining regular exercise and a balanced diet for optimal health.",
            'elevated': "Some of your vital signs show elevated levels. Consider lifestyle modifications and consult with your healthcare provider.",
            'high': "Several vital signs indicate increased health risks. Please schedule a consultation with your doctor for proper evaluation.",
            'critical': "Your vital signs show critical levels that require immediate medical attention. Please contact your healthcare provider immediately."
        }
        
        return messages.get(risk_level, "Please consult with your healthcare provider for a comprehensive health assessment.")
    
    def get_risk_trend(self):
        """Get risk trend indicator (up, down, stable)"""
        # For now, return a default trend - this could be enhanced with historical data
        risk_level = self.calculate_risk_level()
        
        if risk_level in ['low', 'normal']:
            return 'down'  # Positive trend
        elif risk_level == 'elevated':
            return 'stable'
        else:
            return 'up'  # Concerning trend
    
    def save(self, *args, **kwargs):
        """Override save to automatically calculate risk level"""
        self.overall_risk_level = self.calculate_risk_level()
        super().save(*args, **kwargs)


class VitalSignAlert(models.Model):
    """
    Model to track alerts generated for high-risk vital signs
    """
    ALERT_TYPE_CHOICES = [
        ('high_bp', _('High Blood Pressure')),
        ('low_bp', _('Low Blood Pressure')),
        ('high_hr', _('High Heart Rate')),
        ('low_hr', _('Low Heart Rate')),
        ('high_temp', _('High Temperature')),
        ('low_temp', _('Low Temperature')),
        ('low_o2', _('Low Oxygen Saturation')),
        ('critical_vitals', _('Critical Vitals')),
        ('cardiovascular_risk', _('High Cardiovascular Risk')),
    ]
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('acknowledged', _('Acknowledged')),
        ('resolved', _('Resolved')),
    ]
    
    vital_sign = models.ForeignKey(
        VitalSign,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_('Vital Sign Record')
    )
    
    alert_type = models.CharField(
        max_length=30,
        choices=ALERT_TYPE_CHOICES,
        verbose_name=_('Alert Type')
    )
    
    severity = models.CharField(
        max_length=20,
        choices=VitalSign.RISK_LEVEL_CHOICES,
        verbose_name=_('Severity')
    )
    
    message = models.TextField(
        verbose_name=_('Alert Message')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=_('Status')
    )
    
    notified_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='received_vital_alerts',
        verbose_name=_('Notified Users')
    )
    
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_vital_alerts',
        verbose_name=_('Acknowledged By')
    )
    
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Acknowledged At')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    class Meta:
        verbose_name = _('Vital Sign Alert')
        verbose_name_plural = _('Vital Sign Alerts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['severity']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.vital_sign.patient} - {self.get_severity_display()}"