from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom user model for Laso Healthcare system.
    Each user can be a patient, doctor, receptionist, or admin.
    """
    USER_TYPE_CHOICES = [
        ('patient', _('Patient')),
        ('doctor', _('Doctor')),
        ('receptionist', _('Receptionist')),
        ('admin', _('Admin')),
    ]
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='patient',
        verbose_name=_('User Type')
    )

    # SaaS / Multi-Hospital Fields
    hospital = models.ForeignKey(
        'core.Hospital',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('Hospital')
    )
    
    department = models.ForeignKey(
        'core.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff',
        verbose_name=_('Department'),
        help_text=_('For detailed staff assignment (e.g. Cardiology)')
    )
    
    # Additional fields for doctors
    specialization = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name=_('Specialization')
    )
    
    # Profile picture
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        verbose_name=_('Profile Picture')
    )
    
    # Additional fields for patients
    date_of_birth = models.DateField(
        blank=True, 
        null=True, 
        verbose_name=_('Date of Birth')
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name=_('Phone Number')
    )
    address = models.TextField(
        blank=True, 
        null=True,
        verbose_name=_('Address')
    )
    blood_type = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        verbose_name=_('Blood Type')
    )
    
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
    ]
    
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name=_('Gender')
    )
    
    def is_patient(self):
        return self.user_type == 'patient'
    
    def is_doctor(self):
        return self.user_type == 'doctor'
    
    def is_receptionist(self):
        return self.user_type == 'receptionist'
    
    def is_admin_user(self):
        return self.user_type == 'admin'
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
