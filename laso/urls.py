"""
URL configuration for laso project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from core.forms import LoginForm
from core.views import HomeView, dashboard
from core.views_auth import CustomLoginView, HomeRedirectView
from core.logout_view import logout_view
from core.admin_login import AdminLoginView
from core.test_login import test_admin_login
from core.views_theme import toggle_theme, get_theme_preference
from core.health_check import health_check, readiness_check, liveness_check
from core import views_debug
urlpatterns = [
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
    path('test-admin-login/', test_admin_login, name='test_admin_login'),
    path('admin/', admin.site.urls),
    
    # Home page - redirect to login if not authenticated, otherwise to dashboard
    path('', HomeRedirectView.as_view(), name='home'),
    path('landing/', HomeView.as_view(), name='landing'),
    
    # Dashboard - main dashboard endpoint
    path('dashboard/', dashboard, name='dashboard'),
    
    # Add catch-all for login/dashboard redirect fix
    path('login/dashboard/', RedirectView.as_view(pattern_name='dashboard', permanent=True)),
    
    # Authentication
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', include([
        path('', RedirectView.as_view(pattern_name='core:patient-register', permanent=True), name='register'),
        path('patient/', RedirectView.as_view(pattern_name='core:patient-register', permanent=True), name='patient-register'),
    ])),
    
    # Theme settings
    path('theme/toggle/', toggle_theme, name='toggle-theme'),
    path('theme/preference/', get_theme_preference, name='get-theme-preference'),
    
    # Health check endpoints
    path('health/', health_check, name='health-check'),
    path('readiness/', readiness_check, name='readiness-check'),
    path('liveness/', liveness_check, name='liveness-check'),
    
    # Debug endpoints (remove in production)
    path('debug/auth/', include([
        path('', views_debug.debug_auth, name='debug-auth'),
        path('user/', views_debug.debug_user, name='debug-user'),
    ])),
    
    # Core application URLs
    path('core/', include('core.urls', namespace='core')),
    
    # Appointments application URLs
    path('appointments/', include('appointments.urls')),
    
    # Treatments application URLs
    path('treatments/', include('treatments.urls')),
    
    # Telemedicine application URLs
    path('telemedicine/', include('telemedicine.urls')),
]

# URLs for media and static files
# Always add media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Add static files in debug mode or when not using WhiteNoise
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Configure admin site login URL
admin.site.login_url = '/admin/login/'
from core.test_login import test_admin_login
path('test-admin-login/', test_admin_login, name='test_admin_login'),
