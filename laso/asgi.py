"""
ASGI config for laso project with WebSocket support.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Import WebSocket routing
websocket_urlpatterns = []

try:
    from telemedicine.routing import websocket_urlpatterns as telemedicine_patterns
    websocket_urlpatterns.extend(telemedicine_patterns)
except ImportError:
    pass

try:
    from treatments.vitals_routing import websocket_urlpatterns as vitals_patterns
    websocket_urlpatterns.extend(vitals_patterns)
except ImportError:
    pass

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
