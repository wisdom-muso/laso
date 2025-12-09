from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'telemedicine'

urlpatterns = [
    # Main views
    path('', views.TeleMedicineConsultationListView.as_view(), name='list'),
    path('schedule/', views.TeleMedicineConsultationCreateView.as_view(), name='schedule'),
    path('session/<str:session_id>/', views.TeleMedicineConsultationDetailView.as_view(), name='detail'),
    path('session/<str:session_id>/join/', views.TeleMedicineConsultationJoinView.as_view(), name='join'),
    path('session/<int:consultation_id>/end/', views.end_consultation, name='end'),
    
    # AJAX/API views
    path('session/<int:consultation_id>/send-message/', views.send_consultation_message, name='send_message'),
    path('session/<int:consultation_id>/get-messages/', views.get_consultation_messages, name='get_messages'),
    path('session/<int:consultation_id>/update-status/', views.update_consultation_status, name='update_status'),
    
    # Settings
    path('settings/', views.TeleMedicineSettingsView.as_view(), name='settings'),
    
    # Analytics
    path('analytics/', views.TeleconsultationAnalyticsView.as_view(), name='analytics'),
    
    # WebRTC signaling (for future implementation)
    path('session/<str:session_id>/signal/', views.webrtc_signal, name='webrtc_signal'),

    # Appointment views
    path('appointments/', views.TelemedicineAppointmentListView.as_view(), name='appointment-list'),
    path('appointment/<int:pk>/', views.TelemedicineAppointmentDetailView.as_view(), name='appointment-detail'),
    path('appointment/<int:appointment_id>/start-video-session/', views.start_video_session, name='start-video-session'),
    path('video-session/<int:session_id>/end/', views.end_video_session, name='end-video-session'),
    path('appointment/<int:appointment_id>/upload-document/', views.upload_telemed_document, name='upload-document'),
    path('appointment/<int:appointment_id>/create-prescription/', views.create_telemed_prescription, name='create-prescription'),
    path('appointment/<int:appointment_id>/create-note/', views.create_telemed_note, name='create-note'),
    
    # Direct messaging URLs
    path('messages/', views.DoctorMessagingDashboardView.as_view(), name='doctor-messages'),
    path('patient-messages/', RedirectView.as_view(pattern_name='dashboard', permanent=True), name='patient-messages'),
    path('thread/<int:pk>/', views.MessageThreadDetailView.as_view(), name='message-thread'),
    path('api/send-message/', views.send_direct_message, name='send-direct-message'),
    path('api/threads/', views.get_message_threads, name='get-message-threads'),
    path('api/thread/<int:thread_id>/messages/', views.get_thread_messages, name='get-thread-messages'),
    path('api/start-call/', views.start_direct_call, name='start-direct-call'),
]
