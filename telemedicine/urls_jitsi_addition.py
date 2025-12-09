"""
Add these URL patterns to your existing telemedicine/urls.py
"""
from django.urls import path
from . import views_jitsi

# Add these to your existing urlpatterns list:
jitsi_urlpatterns = [
    # Jitsi Meet Integration URLs
    path('jitsi/<int:appointment_id>/', views_jitsi.jitsi_telemedicine_room, name='jitsi-room'),
    path('appointment/<int:appointment_id>/toggle-telemedicine/', views_jitsi.toggle_telemedicine, name='toggle-telemedicine'),
    path('appointment/<int:appointment_id>/check-status/', views_jitsi.check_telemedicine_status, name='check-telemedicine-status'),
    path('appointment/<int:appointment_id>/detail/', views_jitsi.appointment_detail_with_telemedicine, name='appointment-detail-telemedicine'),
]

# Or add to main project urls.py:
# path('telemedicine/jitsi/<int:appointment_id>/', views_jitsi.jitsi_telemedicine_room, name='jitsi-telemedicine-room'),
# path('appointments/<int:appointment_id>/toggle-telemedicine/', views_jitsi.toggle_telemedicine, name='toggle-telemedicine'),
# path('appointments/<int:appointment_id>/telemedicine-status/', views_jitsi.check_telemedicine_status, name='check-telemedicine-status'),
