"""
Jitsi Meet Integration Views for Telemedicine
Add these views to your existing telemedicine/views.py or create as separate file
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import json

from appointments.models import Appointment


@login_required
def jitsi_telemedicine_room(request, appointment_id):
    """
    Jitsi Meet telemedicine room view
    Only allows access to doctor and patient within valid time window
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if user can join this call
    if not appointment.can_user_join_call(request.user):
        messages.error(request, _('You are not authorized to join this telemedicine session.'))
        return redirect('dashboard')
    
    # Check if call is available
    is_available, message = appointment.is_available_for_call()
    
    context = {
        'appointment': appointment,
        'is_available': is_available,
        'availability_message': message,
        'jitsi_domain': getattr(settings, 'JITSI_MEET_DOMAIN', 'meet.jit.si'),
        'user_display_name': request.user.get_full_name() or request.user.username,
        'user_role': 'Doctor' if hasattr(request.user, 'is_doctor') and request.user.is_doctor() else 'Patient',
    }
    
    # If available, generate room name
    if is_available:
        context['room_name'] = appointment.get_jitsi_room_name()
        context['jitsi_config'] = {
            'roomName': context['room_name'],
            'width': '100%',
            'height': '600',
            'parentNode': 'jitsi-container',
            'userInfo': {
                'displayName': context['user_display_name']
            },
            'configOverwrite': {
                'startWithAudioMuted': False,
                'startWithVideoMuted': False,
                'enableWelcomePage': False,
                'prejoinPageEnabled': False,
                'disableInviteFunctions': True,
            },
            'interfaceConfigOverwrite': {
                'TOOLBAR_BUTTONS': [
                    'microphone', 'camera', 'closedcaptions', 'desktop',
                    'fullscreen', 'fodeviceselection', 'hangup', 'profile',
                    'chat', 'recording', 'livestreaming', 'etherpad',
                    'sharedvideo', 'settings', 'raisehand', 'videoquality',
                    'filmstrip', 'invite', 'feedback', 'stats', 'shortcuts',
                    'tileview', 'videobackgroundblur', 'download', 'help',
                    'mute-everyone', 'security'
                ],
                'SETTINGS_SECTIONS': ['devices', 'language', 'moderator', 'profile', 'calendar'],
                'SHOW_JITSI_WATERMARK': False,
                'SHOW_WATERMARK_FOR_GUESTS': False,
                'SHOW_BRAND_WATERMARK': False,
                'BRAND_WATERMARK_LINK': '',
                'SHOW_POWERED_BY': False,
                'DEFAULT_BACKGROUND': '#474747',
            }
        }
    else:
        context['time_until_available'] = appointment.time_until_available()
    
    return render(request, 'telemedicine/jitsi_room.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_telemedicine(request, appointment_id):
    """
    Toggle telemedicine status for an appointment
    Only doctors can enable/disable telemedicine for appointments
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if user is the doctor for this appointment
    if request.user != appointment.doctor:
        return JsonResponse({
            'success': False,
            'message': 'Only the assigned doctor can modify telemedicine settings.'
        }, status=403)
    
    # Toggle telemedicine status
    appointment.is_telemedicine = not appointment.is_telemedicine
    appointment.save(update_fields=['is_telemedicine'])
    
    return JsonResponse({
        'success': True,
        'is_telemedicine': appointment.is_telemedicine,
        'message': f'Telemedicine {"enabled" if appointment.is_telemedicine else "disabled"} for this appointment.'
    })


@login_required
def check_telemedicine_status(request, appointment_id):
    """
    AJAX endpoint to check telemedicine availability status
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if user can join this call
    if not appointment.can_user_join_call(request.user):
        return JsonResponse({
            'success': False,
            'message': 'Unauthorized access.'
        }, status=403)
    
    is_available, message = appointment.is_available_for_call()
    
    return JsonResponse({
        'success': True,
        'is_available': is_available,
        'message': message,
        'time_until_available': appointment.time_until_available() if not is_available else 0,
        'room_name': appointment.get_jitsi_room_name() if is_available else None
    })


@login_required
def appointment_detail_with_telemedicine(request, appointment_id):
    """
    Enhanced appointment detail view with telemedicine integration
    This can replace or extend your existing appointment detail view
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if user can view this appointment
    if not (request.user == appointment.doctor or request.user == appointment.patient):
        messages.error(request, _('You are not authorized to view this appointment.'))
        return redirect('dashboard')
    
    is_available, availability_message = appointment.is_available_for_call()
    
    context = {
        'appointment': appointment,
        'is_telemedicine_available': is_available,
        'telemedicine_message': availability_message,
        'can_toggle_telemedicine': request.user == appointment.doctor,
        'time_until_available': appointment.time_until_available(),
    }
    
    return render(request, 'appointments/appointment_detail_telemedicine.html', context)
