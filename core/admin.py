from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.urls import path
from django.shortcuts import redirect
from users.models import User
from .models_theme import UserThemePreference
from .models_statistics import DoctorPerformanceMetric
from .models_communication import CommunicationNotification, Message, EmailTemplate
from .models_notifications import Notification, NotificationType, NotificationTemplate, NotificationLog
from .models_sessions import LoginSession
from .models_organization import Hospital, Department
from .admin_dashboard import admin_dashboard

# Import AI admin configurations
from .admin_ai import AIConfigurationAdmin, AIConversationAdmin, AIPromptTemplateAdmin

# Using Django's default admin site with Unfold integration

class CommunicationNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__email', 'title', 'message')
    date_hierarchy = 'created_at'

class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'subject', 'content')
    date_hierarchy = 'created_at'

class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'subject', 'is_active')
    list_filter = ('template_type', 'is_active', 'created_at')
    search_fields = ('name', 'subject', 'content')
    date_hierarchy = 'created_at'

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'priority', 'created_at')
    search_fields = ('recipient__username', 'recipient__email', 'title', 'message')
    date_hierarchy = 'created_at'

class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'is_active')
    list_filter = ('notification_type', 'is_active')
    search_fields = ('title_template', 'message_template')

class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('notification', 'delivery_method', 'status', 'sent_at')
    list_filter = ('delivery_method', 'status', 'sent_at')
    search_fields = ('notification__title', 'error_message')
    date_hierarchy = 'sent_at'

class DoctorPerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'appointments_count', 'treatments_count', 'average_rating')
    list_filter = ('date',)
    search_fields = ('doctor__username', 'doctor__first_name', 'doctor__last_name')
    date_hierarchy = 'date'

class UserThemePreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'sidebar_mode', 'updated_at')
    list_filter = ('theme', 'sidebar_mode')
    search_fields = ('user__username', 'user__email')

class LoginSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'logout_time', 'duration_display', 'ip_address', 'is_active')
    list_filter = ('is_active', 'login_time', 'user__user_type')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'ip_address')
    date_hierarchy = 'login_time'
    readonly_fields = ('duration_display', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

# Register all models with the default admin site
# Note: User is already registered in users/admin.py
admin.site.register(CommunicationNotification, CommunicationNotificationAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(EmailTemplate, EmailTemplateAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationTemplate, NotificationTemplateAdmin)
admin.site.register(NotificationLog, NotificationLogAdmin)
admin.site.register(DoctorPerformanceMetric, DoctorPerformanceMetricAdmin)
admin.site.register(UserThemePreference, UserThemePreferenceAdmin)
admin.site.register(LoginSession, LoginSessionAdmin)
admin.site.register(Hospital)
admin.site.register(Department)

# Import Enterprise Features Admin
from . import admin_enterprise
