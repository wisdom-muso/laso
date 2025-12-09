"""
Organization Models for Multi-Tenant SaaS Architecture
Includes Hospital and Department management
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils.text import slugify


class Hospital(models.Model):
    """
    Hospital/Tenant model for SaaS architecture.
    All data will be scoped to a specific hospital.
    """
    name = models.CharField(
        max_length=200,
        verbose_name=_('Hospital Name')
    )
    
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text=_('Unique identifier for URL routing (e.g., st-marys-hospital)')
    )
    
    # Contact Information
    address = models.TextField(
        verbose_name=_('Address')
    )
    
    phone_number = models.CharField(
        max_length=20,
        verbose_name=_('Phone Number')
    )
    
    email = models.EmailField(
        verbose_name=_('Contact Email')
    )
    
    website = models.URLField(
        blank=True,
        verbose_name=_('Website')
    )
    
    # Branding
    logo = models.ImageField(
        upload_to='hospital_logos/',
        null=True,
        blank=True,
        verbose_name=_('Logo')
    )
    
    primary_color = models.CharField(
        max_length=7,
        default='#0d6efd',
        help_text=_('Hex color code (e.g., #0d6efd)'),
        verbose_name=_('Primary Color')
    )
    
    # Subscription/License
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    
    subscription_plan = models.CharField(
        max_length=50,
        choices=[
            ('basic', _('Basic (Small Clinic)')),
            ('standard', _('Standard (Medium Hospital)')),
            ('enterprise', _('Enterprise (Multi-Specialty)')),
        ],
        default='standard',
        verbose_name=_('Subscription Plan')
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
        verbose_name = _('Hospital')
        verbose_name_plural = _('Hospitals')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Department(models.Model):
    """
    Medical Departments within a Hospital (e.g., Cardiology, Neurology)
    """
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name=_('Hospital')
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('Department Name')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    head_of_department = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
        verbose_name=_('Head of Department'),
        limit_choices_to={'user_type': 'doctor'}
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    class Meta:
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')
        unique_together = ['hospital', 'name']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.hospital.name}"
