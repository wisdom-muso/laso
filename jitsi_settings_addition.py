# Add this to your laso/settings.py file

# Jitsi Meet Configuration
JITSI_DOMAIN = "meet.jit.si"  # Can be changed to self-hosted domain later

# Updated Telemedicine Settings with Jitsi integration
TELEMEDICINE_SETTINGS = {
    'MAX_SESSION_DURATION': 120,  # minutes
    'DEFAULT_SESSION_DURATION': 30,  # minutes
    'WEBRTC_STUN_SERVERS': [
        'stun:stun.l.google.com:19302',
        'stun:stun1.l.google.com:19302',
    ],
    'RECORDING_ENABLED': True,
    'RECORDING_PATH': MEDIA_ROOT + '/recordings/',
    'AUTO_END_SESSION_AFTER': 150,  # minutes
    'JITSI_DOMAIN': JITSI_DOMAIN,
    'CALL_WINDOW_BEFORE': 10,  # minutes before appointment
    'CALL_WINDOW_AFTER': 30,   # minutes after appointment
    'ENABLE_JITSI_INTEGRATION': True,
}
