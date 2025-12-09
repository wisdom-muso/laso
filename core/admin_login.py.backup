from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import RedirectView
from .forms import LoginForm


class AdminLoginView(LoginView):
    """
    Custom admin login view that redirects to admin panel after successful login
    """
    template_name = 'admin/login.html'
    form_class = LoginForm
    
    def get_success_url(self):
        """
        Always redirect to admin panel after successful admin login
        """
        # Check if there's a 'next' parameter for admin URLs
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        
        if next_url and next_url.startswith('/admin/'):
            return next_url
        
        # Default to admin index
        return '/admin/'
    
    def form_valid(self, form):
        """
        Security check complete. Log the user in and redirect to admin.
        """
        user = form.get_user()
        
        # Debug logging
        print(f"DEBUG: Admin login attempt for user: {user.username}, is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")
        
        # Check if user has admin access
        if not (user.is_staff or user.is_superuser):
            form.add_error(None, 'You do not have permission to access the admin panel.')
            return self.form_invalid(form)
        
        return super().form_valid(form)


class AdminRedirectView(RedirectView):
    """
    Custom redirect view for admin access that checks authentication
    """
    permanent = False
    
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser):
            return '/admin/'
        else:
            return f'/admin/login/?next={self.request.path}'