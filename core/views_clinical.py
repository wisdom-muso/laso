"""
Clinical Views for Doctors
Includes SOAP Notes management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models_soap_notes import SOAPNote
from .models_adt import PatientAdmission

User = get_user_model()

class DoctorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_doctor() or self.request.user.is_admin_user()

class SOAPNoteListView(LoginRequiredMixin, DoctorRequiredMixin, ListView):
    model = SOAPNote
    template_name = 'core/clinical/soap_note_list.html'
    context_object_name = 'soap_notes'
    paginate_by = 10

    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        return SOAPNote.objects.filter(patient_id=patient_id).order_by('-encounter_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = get_object_or_404(User, pk=self.kwargs.get('patient_id'))
        return context

class SOAPNoteCreateView(LoginRequiredMixin, DoctorRequiredMixin, CreateView):
    model = SOAPNote
    template_name = 'core/clinical/soap_note_form.html'
    fields = [
        'encounter_type', 'chief_complaint', 
        'history_of_present_illness', 'symptom_onset', 'symptom_severity', 'review_of_systems',
        'vital_signs_summary', 'physical_examination',
        'primary_diagnosis', 'differential_diagnoses', 'clinical_impression',
        'treatment_plan', 'medications_prescribed', 'follow_up_instructions'
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = get_object_or_404(User, pk=self.kwargs.get('patient_id'))
        return context

    def form_valid(self, form):
        patient = get_object_or_404(User, pk=self.kwargs.get('patient_id'))
        form.instance.patient = patient
        form.instance.provider = self.request.user
        form.instance.status = 'draft' # Starts as draft
        
        # Link to admission if it exists and is active
        # (Simplified logic, could be enhanced)
        
        response = super().form_valid(form)
        messages.success(self.request, _("SOAP Note saved as draft."))
        return response

    def get_success_url(self):
        return reverse('core:soap-note-list', kwargs={'patient_id': self.kwargs.get('patient_id')})

class SOAPNoteDetailView(LoginRequiredMixin, DoctorRequiredMixin, DetailView):
    model = SOAPNote
    template_name = 'core/clinical/soap_note_detail.html'
    context_object_name = 'note'

    def post(self, request, *args, **kwargs):
        # Handle signing
        note = self.get_object()
        if 'sign' in request.POST:
            if note.provider == request.user:
                note.sign_note()
                messages.success(request, _("Note signed and locked."))
            else:
                messages.error(request, _("Only the provider can sign this note."))
        return redirect('core:soap-note-detail', pk=note.pk)
