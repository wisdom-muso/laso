"""
SaaS Workflows and Enterprise Feature Views
Handles Patient Onboarding, Bed Management, and ADT workflows
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, DetailView, TemplateView, View
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from .forms import PatientOnboardingForm
from .models_bed_management import Ward, Room, Bed
from .models_adt import PatientAdmission
from .models_organization import Hospital, Department

User = get_user_model()

# ==========================================
# SaaS Patient Onboarding (Staff-Driven)
# ==========================================

class PatientOnboardingView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Staff-driven patient registration with auto-credential generation.
    """
    model = User
    form_class = PatientOnboardingForm
    template_name = 'core/saas/patient_onboarding.html'
    success_url = reverse_lazy('core:dashboard') 

    def test_func(self):
        # Only Receptionists, Doctors, or Admins can onboard patients
        user = self.request.user
        return user.is_receptionist() or user.is_doctor() or user.is_admin_user()

    def form_valid(self, form):
        user = form.save(commit=False)
        
        # 1. Auto-generate username (lastname.firstname.random)
        base_username = f"{user.last_name.lower()}.{user.first_name.lower()}"
        random_suffix = get_random_string(4, allowed_chars='0123456789')
        user.username = f"{base_username}.{random_suffix}"
        
        # 2. Auto-generate secure password
        password = get_random_string(10)
        user.set_password(password)
        
        # 3. Link to Organization (Hospital)
        if hasattr(self.request.user, 'hospital'):
             user.hospital = self.request.user.hospital
        
        user.user_type = 'patient'
        user.save()
        
        # 4. Send Credentials via Email
        if user.email:
            try:
                subject = f"Welcome to {user.hospital.name if user.hospital else 'Laso Healthcare'}"
                message = f"""
                Hello {user.first_name},
                
                You have been registered at {user.hospital.name if user.hospital else 'Laso Healthcare'}.
                
                Here are your login credentials:
                Username: {user.username}
                Password: {password}
                
                Please login at: {self.request.build_absolute_uri(reverse_lazy('login'))}
                
                Stay healthy!
                """
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
                messages.success(self.request, _(f"Patient {user.get_full_name()} onboarded. Credentials sent to {user.email}."))
            except Exception as e:
                messages.warning(self.request, _(f"Patient created, but email failed: {e}. Password is: {password}"))
        else:
             messages.success(self.request, _(f"Patient created. No email provided. Password is: {password}"))
             
        return redirect(self.success_url)


# ==========================================
# Bed Management Frontend Views
# ==========================================

class BedManagementDashboardView(LoginRequiredMixin, TemplateView):
    """
    Overview of Hospital Wards and Occupancy
    """
    template_name = 'core/bed_management/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filter details by hospital if applicable
        wards = Ward.objects.all()
        # if self.request.user.hospital:
        #    wards = wards.filter(hospital=self.request.user.hospital) # Note: Ward model needs hospital link in future
            
        context['wards'] = wards
        context['total_beds'] = Bed.objects.filter(is_active=True).count()
        context['occupied_beds'] = Bed.objects.filter(status='occupied').count()
        context['available_beds'] = Bed.objects.filter(status='available').count()
        
        return context

class WardDetailView(LoginRequiredMixin, DetailView):
    model = Ward
    template_name = 'core/bed_management/ward_detail.html'
    context_object_name = 'ward'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Group beds by room
        context['rooms'] = self.object.rooms.all().prefetch_related('beds')
        return context


# ==========================================
# ADT Workflow Views
# ==========================================

class AdmissionCreateView(LoginRequiredMixin, CreateView):
    model = PatientAdmission
    fields = ['patient', 'admission_type', 'admission_diagnosis', 'bed', 'notes'] # Simplified for demo
    template_name = 'core/adt/admission_form.html'
    success_url = reverse_lazy('core:bed-dashboard')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter patients and beds
        form.fields['patient'].queryset = User.objects.filter(user_type='patient')
        form.fields['bed'].queryset = Bed.objects.filter(status='available')
        return form

    def form_valid(self, form):
        admission = form.save(commit=False)
        admission.admitting_doctor = self.request.user
        admission.save()
        
        # Confirm bed occupancy
        if admission.bed:
            admission.bed.mark_occupied(admission.patient)
            
        messages.success(self.request, _("Patient successfully admitted."))
        return redirect(self.success_url)
