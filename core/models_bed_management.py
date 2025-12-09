"""
Hospital Bed Management Models for Laso Healthcare
Includes Ward, Room, and Bed management with occupancy tracking
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Ward(models.Model):
    """
    Hospital ward/department model
    """
    WARD_TYPE_CHOICES = [
        ('general', _('General Ward')),
        ('icu', _('Intensive Care Unit (ICU)')),
        ('nicu', _('Neonatal ICU')),
        ('picu', _('Pediatric ICU')),
        ('ccu', _('Cardiac Care Unit')),
        ('emergency', _('Emergency Ward')),
        ('surgical', _('Surgical Ward')),
        ('maternity', _('Maternity Ward')),
        ('pediatric', _('Pediatric Ward')),
        ('psychiatric', _('Psychiatric Ward')),
        ('isolation', _('Isolation Ward')),
        ('burns', _('Burns Unit')),
        ('oncology', _('Oncology Ward')),
        ('orthopedic', _('Orthopedic Ward')),
        ('neurology', _('Neurology Ward')),
        ('cardiology', _('Cardiology Ward')),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('Ward Name')
    )
    
    ward_type = models.CharField(
        max_length=20,
        choices=WARD_TYPE_CHOICES,
        default='general',
        verbose_name=_('Ward Type')
    )
    
    floor = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Floor Number')
    )
    
    building = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Building')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    head_nurse = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_wards',
        verbose_name=_('Head Nurse'),
        limit_choices_to={'user_type__in': ['doctor', 'admin']}
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
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
        verbose_name = _('Ward')
        verbose_name_plural = _('Wards')
        ordering = ['floor', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_ward_type_display()}) - Floor {self.floor}"
    
    @property
    def total_beds(self):
        """Total number of beds in this ward"""
        return Bed.objects.filter(room__ward=self, is_active=True).count()
    
    @property
    def available_beds(self):
        """Number of available beds in this ward"""
        return Bed.objects.filter(room__ward=self, is_active=True, status='available').count()
    
    @property
    def occupancy_rate(self):
        """Current occupancy rate percentage"""
        total = self.total_beds
        if total == 0:
            return 0
        occupied = Bed.objects.filter(room__ward=self, is_active=True, status='occupied').count()
        return round((occupied / total) * 100, 1)


class Room(models.Model):
    """
    Hospital room model
    """
    ROOM_TYPE_CHOICES = [
        ('private', _('Private Room')),
        ('semi_private', _('Semi-Private (2 beds)')),
        ('general', _('General Ward (4+ beds)')),
        ('isolation', _('Isolation Room')),
        ('icu', _('ICU Room')),
        ('emergency', _('Emergency Bay')),
        ('operating', _('Operating Room')),
        ('recovery', _('Recovery Room')),
    ]
    
    ward = models.ForeignKey(
        Ward,
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name=_('Ward')
    )
    
    room_number = models.CharField(
        max_length=20,
        verbose_name=_('Room Number')
    )
    
    room_type = models.CharField(
        max_length=20,
        choices=ROOM_TYPE_CHOICES,
        default='general',
        verbose_name=_('Room Type')
    )
    
    capacity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name=_('Bed Capacity')
    )
    
    has_bathroom = models.BooleanField(
        default=False,
        verbose_name=_('Has Bathroom')
    )
    
    has_tv = models.BooleanField(
        default=False,
        verbose_name=_('Has TV')
    )
    
    has_ac = models.BooleanField(
        default=True,
        verbose_name=_('Has Air Conditioning')
    )
    
    daily_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Daily Rate')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
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
        verbose_name = _('Room')
        verbose_name_plural = _('Rooms')
        ordering = ['ward', 'room_number']
        unique_together = ['ward', 'room_number']
    
    def __str__(self):
        return f"Room {self.room_number} - {self.ward.name}"
    
    @property
    def available_beds(self):
        """Number of available beds in this room"""
        return self.beds.filter(is_active=True, status='available').count()
    
    @property
    def is_full(self):
        """Check if room is at full capacity"""
        return self.available_beds == 0


class Bed(models.Model):
    """
    Individual bed model with status tracking
    """
    BED_STATUS_CHOICES = [
        ('available', _('Available')),
        ('occupied', _('Occupied')),
        ('reserved', _('Reserved')),
        ('maintenance', _('Under Maintenance')),
        ('cleaning', _('Being Cleaned')),
    ]
    
    BED_TYPE_CHOICES = [
        ('standard', _('Standard Bed')),
        ('electric', _('Electric Adjustable')),
        ('icu', _('ICU Bed')),
        ('bariatric', _('Bariatric Bed')),
        ('pediatric', _('Pediatric Bed')),
        ('maternity', _('Maternity Bed')),
        ('stretcher', _('Stretcher/Gurney')),
    ]
    
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='beds',
        verbose_name=_('Room')
    )
    
    bed_number = models.CharField(
        max_length=20,
        verbose_name=_('Bed Number/Label')
    )
    
    bed_type = models.CharField(
        max_length=20,
        choices=BED_TYPE_CHOICES,
        default='standard',
        verbose_name=_('Bed Type')
    )
    
    status = models.CharField(
        max_length=20,
        choices=BED_STATUS_CHOICES,
        default='available',
        verbose_name=_('Status')
    )
    
    current_patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_beds',
        verbose_name=_('Current Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    
    has_oxygen = models.BooleanField(
        default=True,
        verbose_name=_('Has Oxygen Supply')
    )
    
    has_suction = models.BooleanField(
        default=False,
        verbose_name=_('Has Suction')
    )
    
    has_monitor = models.BooleanField(
        default=False,
        verbose_name=_('Has Patient Monitor')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    
    last_cleaned = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last Cleaned')
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
        verbose_name = _('Bed')
        verbose_name_plural = _('Beds')
        ordering = ['room', 'bed_number']
        unique_together = ['room', 'bed_number']
    
    def __str__(self):
        return f"Bed {self.bed_number} - Room {self.room.room_number} ({self.get_status_display()})"
    
    @property
    def full_location(self):
        """Full location description"""
        return f"{self.room.ward.name} > Room {self.room.room_number} > Bed {self.bed_number}"
    
    def mark_occupied(self, patient):
        """Mark bed as occupied by patient"""
        self.status = 'occupied'
        self.current_patient = patient
        self.save()
    
    def mark_available(self):
        """Mark bed as available (triggers cleaning status first)"""
        self.status = 'cleaning'
        self.current_patient = None
        self.save()
    
    def mark_cleaned(self):
        """Mark bed as cleaned and available"""
        self.status = 'available'
        self.last_cleaned = timezone.now()
        self.save()
