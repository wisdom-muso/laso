"""
Telemedicine Models for Laso Healthcare
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.core.validators import URLValidator
from appointments.models import Appointment
import uuid
from datetime import datetime


class TelemedicineAppointment(models.Model):
    """
    Telemedicine appointment model
    """
    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telemedicine_patient_appointments',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telemedicine_doctor_appointments',
        verbose_name=_('Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    
    date = models.DateField(
        verbose_name=_('Date')
    )
    
    time = models.TimeField(
        verbose_name=_('Time')
    )
    
    duration = models.PositiveIntegerField(
        default=30,
        verbose_name=_('Duration (minutes)')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name=_('Status')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    chief_complaint = models.TextField(
        blank=True,
        verbose_name=_('Chief Complaint')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_telemedicine_appointments',
        verbose_name=_('Created By')
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
        verbose_name = _('Telemedicine Appointment')
        verbose_name_plural = _('Telemedicine Appointments')
        ordering = ['-date', '-time']
    
    def __str__(self):
        return f"{self.patient} - Dr. {self.doctor} - {self.date} {self.time}"
    
    def is_past(self):
        """Is the appointment in the past?"""
        now = timezone.now()
        appointment_datetime = timezone.make_aware(datetime.combine(self.date, self.time))
        return appointment_datetime < now


class VideoSession(models.Model):
    """
    Video consultation session model
    """
    appointment = models.ForeignKey(
        TelemedicineAppointment,
        on_delete=models.CASCADE,
        related_name='video_sessions',
        verbose_name=_('Appointment')
    )
    
    room_name = models.CharField(
        max_length=255,
        verbose_name=_('Room Name')
    )
    
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='started_sessions',
        verbose_name=_('Started By')
    )
    
    start_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Start Time')
    )
    
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('End Time')
    )
    
    ended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ended_sessions',
        verbose_name=_('Ended By')
    )
    
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Duration (seconds)')
    )
    
    recording_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('Recording URL')
    )
    
    connection_quality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', _('Excellent')),
            ('good', _('Good')),
            ('fair', _('Fair')),
            ('poor', _('Poor')),
        ],
        blank=True,
        null=True,
        verbose_name=_('Connection Quality')
    )
    
    class Meta:
        verbose_name = _('Video Session')
        verbose_name_plural = _('Video Sessions')
        ordering = ['-start_time']
    
    def __str__(self):
        return f"Session: {self.appointment} - {self.start_time}"
    
    def get_duration(self):
        """Calculate session duration"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def save(self, *args, **kwargs):
        if self.end_time and not self.duration_seconds:
            self.duration_seconds = self.get_duration()
        super().save(*args, **kwargs)


class TelemedDocument(models.Model):
    """
    Telemedicine document model
    """
    appointment = models.ForeignKey(
        TelemedicineAppointment,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Appointment')
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title')
    )
    
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('lab_result', _('Lab Result')),
            ('prescription', _('Prescription')),
            ('medical_image', _('Medical Image')),
            ('referral', _('Referral')),
            ('other', _('Other')),
        ],
        verbose_name=_('Document Type')
    )
    
    file = models.FileField(
        upload_to='telemedicine/documents/',
        verbose_name=_('File')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_telemedicine_documents',
        verbose_name=_('Uploaded By')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    class Meta:
        verbose_name = _('Telemedicine Document')
        verbose_name_plural = _('Telemedicine Documents')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.appointment}"


class TelemedPrescription(models.Model):
    """
    Telemedicine prescription model
    """
    appointment = models.ForeignKey(
        TelemedicineAppointment,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        verbose_name=_('Appointment')
    )
    
    medications = models.JSONField(
        verbose_name=_('Medications'),
        help_text=_('Medication list and dosage information')
    )
    
    instructions = models.TextField(
        verbose_name=_('Instructions')
    )
    
    duration_days = models.PositiveIntegerField(
        verbose_name=_('Duration (days)')
    )
    
    is_renewable = models.BooleanField(
        default=False,
        verbose_name=_('Renewable?')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_telemedicine_prescriptions',
        verbose_name=_('Prescribing Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    class Meta:
        verbose_name = _('Telemedicine Prescription')
        verbose_name_plural = _('Telemedicine Prescriptions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prescription: {self.appointment}"


class TelemedNote(models.Model):
    """
    Telemedicine note model
    """
    appointment = models.ForeignKey(
        TelemedicineAppointment,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name=_('Appointment')
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title')
    )
    
    content = models.TextField(
        verbose_name=_('Content')
    )
    
    note_type = models.CharField(
        max_length=50,
        choices=[
            ('diagnosis', _('Diagnosis')),
            ('treatment_plan', _('Treatment Plan')),
            ('follow_up', _('Follow-up')),
            ('general', _('General Note')),
        ],
        default='general',
        verbose_name=_('Note Type')
    )
    
    is_private = models.BooleanField(
        default=False,
        verbose_name=_('Private Note?'),
        help_text=_('Private notes can only be viewed by the doctor')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_telemedicine_notes',
        verbose_name=_('Created By')
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
        verbose_name = _('Telemedicine Note')
        verbose_name_plural = _('Telemedicine Notes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.appointment}"


class TeleMedicineConsultation(models.Model):
    """
    Remote healthcare consultation model
    """
    CONSULTATION_TYPE_CHOICES = [
        ('video', _('Video Call')),
        ('audio', _('Audio Call')),
        ('chat', _('Text Chat')),
        ('hybrid', _('Hybrid (Video + Chat)')),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('waiting', _('Waiting')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
        ('technical_issue', _('Technical Issue')),
    ]
    
    # Basic information
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='telemedicine_consultation',
        verbose_name=_('Appointment')
    )
    
    consultation_type = models.CharField(
        max_length=20,
        choices=CONSULTATION_TYPE_CHOICES,
        default='video',
        verbose_name=_('Consultation Type')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name=_('Status')
    )
    
    # Video conference information
    meeting_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=_('Meeting ID')
    )
    
    meeting_url = models.URLField(
        blank=True,
        verbose_name=_('Meeting URL'),
        help_text=_('Video conference link')
    )
    
    meeting_password = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Meeting Password')
    )
    
    # Platform information
    platform = models.CharField(
        max_length=50,
        choices=[
            ('zoom', 'Zoom'),
            ('teams', 'Microsoft Teams'),
            ('meet', 'Google Meet'),
            ('webex', 'Cisco Webex'),
            ('internal', 'Internal System'),
        ],
        default='internal',
        verbose_name=_('Platform')
    )
    
    # Time information
    scheduled_start_time = models.DateTimeField(
        verbose_name=_('Scheduled Start')
    )
    
    actual_start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Actual Start')
    )
    
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('End Time')
    )
    
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Duration (Minutes)')
    )
    
    # Participant information
    doctor_joined_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Doctor Join Time')
    )
    
    patient_joined_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Patient Join Time')
    )
    
    # Technical details
    connection_quality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', _('Excellent')),
            ('good', _('Good')),
            ('fair', _('Fair')),
            ('poor', _('Poor')),
        ],
        blank=True,
        verbose_name=_('Connection Quality')
    )
    
    technical_issues = models.TextField(
        blank=True,
        verbose_name=_('Technical Issues')
    )
    
    # Consultation details
    consultation_notes = models.TextField(
        blank=True,
        verbose_name=_('Consultation Notes')
    )
    
    # Backward compatibility field
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('General notes about the consultation')
    )
    
    patient_feedback = models.TextField(
        blank=True,
        verbose_name=_('Patient Feedback')
    )
    
    doctor_feedback = models.TextField(
        blank=True,
        verbose_name=_('Doctor Feedback')
    )
    
    # Rating system
    patient_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=[(i, i) for i in range(1, 6)],
        verbose_name=_('Patient Rating (1-5)')
    )
    
    doctor_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=[(i, i) for i in range(1, 6)],
        verbose_name=_('Doctor Rating (1-5)')
    )
    
    # Recording and file sharing
    is_recorded = models.BooleanField(
        default=False,
        verbose_name=_('Recording Made?')
    )
    
    recording_url = models.URLField(
        blank=True,
        verbose_name=_('Recording URL')
    )
    
    shared_files = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Shared Files'),
        help_text=_('List of files shared during consultation')
    )
    
    # Security and privacy
    is_encrypted = models.BooleanField(
        default=True,
        verbose_name=_('Encrypted?')
    )
    
    waiting_room_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Waiting Room Active')
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('Telemedicine Consultation')
        verbose_name_plural = _('Telemedicine Consultations')
        ordering = ['-scheduled_start_time']
    

    def __str__(self):
        return f"{self.appointment.patient} - {self.appointment.doctor} - {self.scheduled_start_time}"
    
    def get_duration(self):
        """Calculate consultation duration in minutes"""
        if self.actual_start_time and self.end_time:
            duration = self.end_time - self.actual_start_time
            return duration.total_seconds() / 60
        return 0
    
    def is_active(self):
        """Is the consultation active?"""
        return self.status == 'in_progress'
    
    def can_join(self, user):
        """Can the user join the consultation?"""
        if self.status not in ['scheduled', 'waiting', 'in_progress']:
            return False
        
        # Only doctor and patient can join
        return user in [self.appointment.doctor, self.appointment.patient]
    
    def get_join_url(self):
        """Generate join URL"""
        if self.meeting_url:
            return self.meeting_url
        
        # Generate URL for internal system
        return f"/telemedicine/join/{self.meeting_id}/"
    
    def mark_as_started(self, user):
        """Mark consultation as started"""
        if not self.actual_start_time:
            self.actual_start_time = timezone.now()
            self.status = 'in_progress'
            
            if user == self.appointment.doctor:
                self.doctor_joined_at = timezone.now()
            elif user == self.appointment.patient:
                self.patient_joined_at = timezone.now()
                
            self.save()
    
    def mark_as_completed(self):
        """Mark consultation as completed"""
        if not self.end_time:
            self.end_time = timezone.now()
            self.status = 'completed'
            
            # Calculate duration
            if self.actual_start_time:
                duration = self.end_time - self.actual_start_time
                self.duration_minutes = int(duration.total_seconds() / 60)
                
            self.save()


class TeleMedicineMessage(models.Model):
    """
    Telemedicine chat messages
    """
    consultation = models.ForeignKey(
        TeleMedicineConsultation,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        verbose_name=_('Consultation')
    )
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Sender')
    )
    
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('text', _('Text')),
            ('file', _('File')),
            ('image', _('Image')),
            ('system', _('System Message')),
        ],
        default='text',
        verbose_name=_('Message Type')
    )
    
    content = models.TextField(
        verbose_name=_('Content')
    )
    
    file_url = models.URLField(
        blank=True,
        verbose_name=_('File URL')
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Is Read?')
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Time')
    )
    
    class Meta:
        verbose_name = _('Telemedicine Message')
        verbose_name_plural = _('Telemedicine Messages')
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender} - {self.timestamp}"


class TeleMedicineSettings(models.Model):
    """
    Telemedicine settings
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telemedicine_settings',
        verbose_name=_('User')
    )
    
    # Video settings
    default_camera_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Default Camera Enabled')
    )
    
    default_microphone_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Default Microphone Enabled')
    )
    
    video_quality = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low (360p)')),
            ('medium', _('Medium (720p)')),
            ('high', _('High (1080p)')),
        ],
        default='medium',
        verbose_name=_('Video Quality')
    )
    
    # Notification settings
    consultation_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Consultation Reminders')
    )
    
    reminder_minutes_before = models.PositiveIntegerField(
        default=15,
        verbose_name=_('Remind Minutes Before')
    )
    
    email_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Email Notifications')
    )
    
    sms_notifications = models.BooleanField(
        default=False,
        verbose_name=_('SMS Notifications')
    )
    
    # Security settings
    require_waiting_room = models.BooleanField(
        default=True,
        verbose_name=_('Waiting Room Required')
    )
    
    allow_recording = models.BooleanField(
        default=False,
        verbose_name=_('Recording Permission')
    )
    
    allow_file_sharing = models.BooleanField(
        default=True,
        verbose_name=_('File Sharing Permission')
    )
    
    # Advanced settings
    max_consultation_duration = models.PositiveIntegerField(
        default=60,
        verbose_name=_('Maximum Consultation Duration (Minutes)')
    )
    
    auto_end_consultation = models.BooleanField(
        default=True,
        verbose_name=_('Auto End')
    )
    
    class Meta:
        verbose_name = _('Telemedicine Settings')
        verbose_name_plural = _('Telemedicine Settings')
    
    def __str__(self):
        return f"{self.user} Settings"


class DoctorPatientMessage(models.Model):
    """
    Direct messaging between doctors and patients outside of consultations
    """
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_patient_messages',
        verbose_name=_('Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_doctor_messages',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_direct_messages',
        verbose_name=_('Sender')
    )
    
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('text', _('Text Message')),
            ('file', _('File Attachment')),
            ('image', _('Image')),
            ('voice', _('Voice Message')),
            ('video_call_request', _('Video Call Request')),
            ('audio_call_request', _('Audio Call Request')),
            ('system', _('System Message')),
        ],
        default='text',
        verbose_name=_('Message Type')
    )
    
    content = models.TextField(
        verbose_name=_('Message Content')
    )
    
    file_attachment = models.FileField(
        upload_to='telemedicine/messages/',
        blank=True,
        null=True,
        verbose_name=_('File Attachment')
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Is Read')
    )
    
    is_urgent = models.BooleanField(
        default=False,
        verbose_name=_('Urgent Message')
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Read At')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    # For call requests
    call_session_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('Call Session ID')
    )
    
    call_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('accepted', _('Accepted')),
            ('declined', _('Declined')),
            ('missed', _('Missed')),
            ('completed', _('Completed')),
        ],
        blank=True,
        null=True,
        verbose_name=_('Call Status')
    )
    
    class Meta:
        verbose_name = _('Doctor-Patient Message')
        verbose_name_plural = _('Doctor-Patient Messages')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['doctor', 'patient', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.get_full_name()} to {self.get_recipient().get_full_name()}: {self.content[:50]}"
    
    def get_recipient(self):
        """Get the recipient of the message"""
        if self.sender == self.doctor:
            return self.patient
        return self.doctor
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class MessageThread(models.Model):
    """
    Message thread between a doctor and patient
    """
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_message_threads',
        verbose_name=_('Doctor'),
        limit_choices_to={'user_type': 'doctor'}
    )
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_message_threads',
        verbose_name=_('Patient'),
        limit_choices_to={'user_type': 'patient'}
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    last_message_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last Message At')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    
    # Unread message counts
    doctor_unread_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Doctor Unread Count')
    )
    
    patient_unread_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Patient Unread Count')
    )
    
    class Meta:
        verbose_name = _('Message Thread')
        verbose_name_plural = _('Message Threads')
        unique_together = ['doctor', 'patient']
        ordering = ['-last_message_at']
    
    def __str__(self):
        return f"Thread: Dr. {self.doctor.get_full_name()} - {self.patient.get_full_name()}"
    
    def get_last_message(self):
        """Get the last message in this thread"""
        return DoctorPatientMessage.objects.filter(
            doctor=self.doctor,
            patient=self.patient
        ).first()
    
    def update_unread_count(self, user):
        """Update unread count for a user"""
        if user == self.doctor:
            self.doctor_unread_count = DoctorPatientMessage.objects.filter(
                doctor=self.doctor,
                patient=self.patient,
                sender=self.patient,
                is_read=False
            ).count()
        else:
            self.patient_unread_count = DoctorPatientMessage.objects.filter(
                doctor=self.doctor,
                patient=self.patient,
                sender=self.doctor,
                is_read=False
            ).count()
        self.save()

