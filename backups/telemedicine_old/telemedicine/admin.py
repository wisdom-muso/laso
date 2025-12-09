from django.contrib import admin
from .models import TeleMedicineConsultation, TeleMedicineMessage, TeleMedicineSettings, DoctorPatientMessage, MessageThread


@admin.register(TeleMedicineConsultation)
class TeleMedicineConsultationAdmin(admin.ModelAdmin):
    list_display = ['meeting_id', 'appointment', 'status', 'scheduled_start_time', 'actual_start_time', 'end_time']
    list_filter = ['status', 'consultation_type', 'scheduled_start_time']
    search_fields = ['meeting_id', 'appointment__patient__username', 'appointment__doctor__username']
    readonly_fields = ['meeting_id', 'actual_start_time', 'end_time']


@admin.register(TeleMedicineMessage)
class TeleMedicineMessageAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'sender', 'message_type', 'timestamp', 'is_read']
    list_filter = ['message_type', 'is_read', 'timestamp']
    search_fields = ['consultation__meeting_id', 'sender__username', 'content']


@admin.register(TeleMedicineSettings)
class TeleMedicineSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'default_camera_enabled', 'default_microphone_enabled', 'video_quality']
    list_filter = ['default_camera_enabled', 'default_microphone_enabled', 'video_quality']
    search_fields = ['user__username']


@admin.register(DoctorPatientMessage)
class DoctorPatientMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'get_recipient', 'message_type', 'is_urgent', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_urgent', 'is_read', 'created_at']
    search_fields = ['doctor__username', 'patient__username', 'sender__username', 'content']
    readonly_fields = ['created_at', 'read_at']
    
    def get_recipient(self, obj):
        return obj.get_recipient().get_full_name()
    get_recipient.short_description = 'Recipient'


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'patient', 'doctor_unread_count', 'patient_unread_count', 'is_active', 'last_message_at']
    list_filter = ['is_active', 'created_at', 'last_message_at']
    search_fields = ['doctor__username', 'patient__username']
    readonly_fields = ['created_at', 'last_message_at']
