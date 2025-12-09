from django.urls import path
from django.views.generic import RedirectView
from . import views
from .views_medical_history import (
    MedicalHistoryListView, MedicalHistoryCreateView, 
    MedicalHistoryUpdateView, MedicalHistoryDeleteView
)
from .views_notification import (
    NotificationListView, mark_notification_as_read, mark_all_notifications_as_read
)
from .views_theme import toggle_theme, get_theme_preference
from .views_dashboard import (
    EnhancedDashboardView, DoctorPerformanceView, SystemReportsView,
    dashboard_analytics_api, patient_health_summary_api, recent_activity,
    export_analytics, enhanced_vitals_dashboard
)
from .views_saas import (
    PatientOnboardingView, BedManagementDashboardView, 
    WardDetailView, AdmissionCreateView
)
from .views_clinical import (
    SOAPNoteListView, SOAPNoteCreateView, SOAPNoteDetailView
)

app_name = 'core'

urlpatterns = [
    # Dashboard
    path('dashboard/', EnhancedDashboardView.as_view(), name='enhanced-dashboard'),
    path('dashboard/doctor-performance/', DoctorPerformanceView.as_view(), name='doctor-performance'),
    path('dashboard/system-reports/', SystemReportsView.as_view(), name='system-reports'),
    
    # Dashboard API endpoints
    path('dashboard/api/analytics/', dashboard_analytics_api, name='dashboard-analytics-api'),
    path('dashboard/api/patient/<int:patient_id>/health-summary/', patient_health_summary_api, name='patient-health-summary-api'),
    path('dashboard/api/recent-activity/', recent_activity, name='recent_activity'),
    path('dashboard/api/export-analytics/', export_analytics, name='export_analytics'),
    
    # Enhanced Vitals Dashboard
    path('vitals/enhanced/', enhanced_vitals_dashboard, name='enhanced-vitals'),
    
    # Alternative dashboard endpoint for API access
    path('api/dashboard/', RedirectView.as_view(pattern_name='dashboard', permanent=True), name='api-dashboard'),

    # Patients
    path('patients/register/', views.PatientRegistrationView.as_view(), name='patient-register'),
    path('patients/', views.PatientListView.as_view(), name='patient-list'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(), name='patient-detail'),
    
    # Doctors
    path('doctors/', views.DoctorListView.as_view(), name='doctor-list'),
    path('doctors/create/', views.DoctorCreationView.as_view(), name='doctor-create'),
    path('doctors/<int:pk>/', views.DoctorDetailView.as_view(), name='doctor-detail'),
    path('doctors/<int:pk>/update/', views.DoctorUpdateView.as_view(), name='doctor-update'),
    
    # Appointments
    path('appointments/', views.AppointmentListView.as_view(), name='appointment-list'),
    path('appointments/create/', views.AppointmentCreateView.as_view(), name='appointment-create'),
    path('appointments/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment-detail'),
    path('appointments/<int:pk>/update/', views.AppointmentUpdateView.as_view(), name='appointment-update'),
    path('appointments/<int:pk>/delete/', views.AppointmentDeleteView.as_view(), name='appointment-delete'),
    
    # Treatments
    path('appointments/<int:appointment_id>/treatment/create/', views.TreatmentCreateView.as_view(), name='treatment-create'),
    path('treatments/<int:pk>/', views.TreatmentDetailView.as_view(), name='treatment-detail'),
    path('treatments/<int:pk>/update/', views.TreatmentUpdateView.as_view(), name='treatment-update'),
    
    # Medical History
    path('patients/<int:patient_id>/medical-history/', MedicalHistoryListView.as_view(), name='medical-history-list'),
    path('patients/<int:patient_id>/medical-history/create/', MedicalHistoryCreateView.as_view(), name='medical-history-create'),
    path('medical-history/<int:pk>/update/', MedicalHistoryUpdateView.as_view(), name='medical-history-update'),
    path('medical-history/<int:pk>/delete/', MedicalHistoryDeleteView.as_view(), name='medical-history-delete'),
    
    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/mark-read/', mark_notification_as_read, name='mark-notification-read'),
    path('notifications/mark-all-read/', mark_all_notifications_as_read, name='mark-all-notifications-read'),
    
    # Theme Settings
    path('theme/toggle/', toggle_theme, name='toggle-theme'),
    path('theme/preference/', get_theme_preference, name='get-theme-preference'),
    
    # Analytics Dashboard
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    
    # AI Assistant
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    
    # Profile Settings
    path('profile/settings/', views.ProfileSettingsView.as_view(), name='profile-settings'),
    
    # Admin Login Sessions
    path('admin/login-sessions/', views.LoginSessionListView.as_view(), name='login-sessions'),
    
    # SaaS / Enterprise Features
    path('hospital/onboard-patient/', PatientOnboardingView.as_view(), name='saas-onboard-patient'),
    path('hospital/beds/', BedManagementDashboardView.as_view(), name='bed-dashboard'),
    path('hospital/beds/ward/<int:pk>/', WardDetailView.as_view(), name='ward-detail'),
    path('hospital/admission/create/', AdmissionCreateView.as_view(), name='admission-create'),
    
    # Clinical Documentation (SOAP Notes)
    path('patients/<int:patient_id>/soap-notes/', SOAPNoteListView.as_view(), name='soap-note-list'),
    path('patients/<int:patient_id>/soap-notes/create/', SOAPNoteCreateView.as_view(), name='soap-note-create'),
    path('soap-notes/<int:pk>/', SOAPNoteDetailView.as_view(), name='soap-note-detail'),
]