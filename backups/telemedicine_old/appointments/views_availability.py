from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models import Q
import calendar
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model

from .models_availability import DoctorAvailability, DoctorTimeOff
from .forms import DoctorAvailabilityForm, DoctorTimeOffForm

User = get_user_model()

class DoctorAvailabilityListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Doctor availability schedule list view.
    """
    model = DoctorAvailability
    template_name = 'appointments/availability_list.html'
    context_object_name = 'availabilities'
    
    def test_func(self):
        # Only the doctor himself, receptionists and admins can see
        user = self.request.user
        doctor_id = self.kwargs.get('doctor_id')
        
        if user.is_doctor():
            return str(user.id) == str(doctor_id)
        return user.is_receptionist() or user.is_admin_user()
    
    def get_queryset(self):
        doctor_id = self.kwargs.get('doctor_id')
        return DoctorAvailability.objects.filter(doctor_id=doctor_id).order_by('weekday', 'start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor_id = self.kwargs.get('doctor_id')
        context['doctor'] = get_object_or_404(User, id=doctor_id)
        context['time_offs'] = DoctorTimeOff.objects.filter(doctor_id=doctor_id).order_by('-start_date')
        return context

class DoctorAvailabilityCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Doctor availability schedule creation view.
    """
    model = DoctorAvailability
    form_class = DoctorAvailabilityForm
    template_name = 'appointments/availability_form.html'
    
    def test_func(self):
        # Only the doctor himself, receptionists and admins can add
        user = self.request.user
        doctor_id = self.kwargs.get('doctor_id')
        
        if user.is_doctor():
            return str(user.id) == str(doctor_id)
        return user.is_receptionist() or user.is_admin_user()
    
    def get_initial(self):
        initial = super().get_initial()
        doctor_id = self.kwargs.get('doctor_id')
        if doctor_id:
            initial['doctor'] = doctor_id
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor_id = self.kwargs.get('doctor_id')
        context['doctor'] = get_object_or_404(User, id=doctor_id)
        context['title'] = _('Add New Working Hour')
        return context
    
    def get_success_url(self):
        return reverse_lazy('doctor-availability-list', kwargs={'doctor_id': self.kwargs.get('doctor_id')})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Working hour added successfully.'))
        return response

class DoctorAvailabilityUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Doctor availability schedule update view.
    """
    model = DoctorAvailability
    form_class = DoctorAvailabilityForm
    template_name = 'appointments/availability_form.html'
    
    def test_func(self):
        # Only the doctor himself, receptionists and admins can update
        user = self.request.user
        availability = self.get_object()
        
        if user.is_doctor():
            return str(user.id) == str(availability.doctor.id)
        return user.is_receptionist() or user.is_admin_user()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctor'] = self.object.doctor
        context['title'] = _('Edit Working Hour')
        return context
    
    def get_success_url(self):
        return reverse_lazy('doctor-availability-list', kwargs={'doctor_id': self.object.doctor.id})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Working hour updated successfully.'))
        return response

class DoctorAvailabilityDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Doctor availability schedule deletion view.
    """
    model = DoctorAvailability
    template_name = 'appointments/availability_confirm_delete.html'
    
    def test_func(self):
        # Only the doctor himself, receptionists and admins can delete
        user = self.request.user
        availability = self.get_object()
        
        if user.is_doctor():
            return str(user.id) == str(availability.doctor.id)
        return user.is_receptionist() or user.is_admin_user()
    
    def get_success_url(self):
        return reverse_lazy('doctor-availability-list', kwargs={'doctor_id': self.object.doctor.id})
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, _('Working hour deleted successfully.'))
        return response

class DoctorCalendarView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Doctor calendar view. Shows the days the doctor is available and off.
    Accessible to both doctors and patients.
    """
    template_name = 'appointments/doctor_calendar.html'
    
    def test_func(self):
        # The doctor himself, patients, receptionists and admins can see
        user = self.request.user
        doctor_id = self.kwargs.get('doctor_id')
        
        if user.is_doctor():
            return str(user.id) == str(doctor_id)
        # Allow access to all patient users
        if user.is_patient():
            return True
        return user.is_receptionist() or user.is_admin_user()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor_id = self.kwargs.get('doctor_id')
        doctor = get_object_or_404(User, id=doctor_id)
        
        # Selected month (defaults to the current month)
        year = self.request.GET.get('year', datetime.now().year)
        month = self.request.GET.get('month', datetime.now().month)
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            year = datetime.now().year
            month = datetime.now().month
            
        # Get month name
        month_name = calendar.month_name[month]
        
        # Create calendar
        cal = calendar.monthcalendar(year, month)
        
        # Get doctor availability information
        availabilities = DoctorAvailability.objects.filter(doctor_id=doctor_id, is_active=True)
        
        # Get doctor time off days
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, calendar.monthrange(year, month)[1]).date()
        time_offs = DoctorTimeOff.objects.filter(
            doctor_id=doctor_id,
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        # Create calendar data
        calendar_data = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:  # Days not in the month
                    week_data.append({'day': '', 'availabilities': [], 'time_offs': []})
                else:
                    date = datetime(year, month, day).date()
                    
                    # Find out which day of the week this day is
                    weekday = date.weekday()
                    
                    # Find available hours for this day
                    day_availabilities = [av for av in availabilities if av.weekday == weekday]
                    
                    # Find time offs for this day
                    day_time_offs = [
                        to for to in time_offs 
                        if to.start_date <= date <= to.end_date
                    ]
                    
                    week_data.append({
                        'day': day, 
                        'date': date,
                        'availabilities': day_availabilities,
                        'time_offs': day_time_offs
                    })
            calendar_data.append(week_data)
        
        # Links for previous and next month
        prev_month = month - 1
        prev_year = year
        if prev_month == 0:
            prev_month = 12
            prev_year = year - 1
            
        next_month = month + 1
        next_year = year
        if next_month == 13:
            next_month = 1
            next_year = year + 1
        
        context.update({
            'doctor': doctor,
            'calendar_data': calendar_data,
            'year': year,
            'month': month,
            'month_name': month_name,
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
            'weekdays': [_('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'), _('Friday'), _('Saturday'), _('Sunday')],
        })
        
        return context

class DoctorTimeOffListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Doctor time off days list view.
    """
    model = DoctorTimeOff
    template_name = 'appointments/timeoff_list.html'
    context_object_name = 'time_offs'
    
    def test_func(self):
        # Only the doctor himself, receptionists and admins can see
        user = self.request.user
        doctor_id = self.kwargs.get('doctor_id')
        
        if user.is_doctor():
            return str(user.id) == str(doctor_id)
        return user.is_receptionist() or user.is_admin_user()
    
    def get_queryset(self):
        doctor_id = self.kwargs.get('doctor_id')
        return DoctorTimeOff.objects.filter(doctor_id=doctor_id).order_by('-start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor_id = self.kwargs.get('doctor_id')
        context['doctor'] = get_object_or_404(User, id=doctor_id)
        return context

class DoctorTimeOffCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Doctor time off day creation view.
    """
    model = DoctorTimeOff
    form_class = DoctorTimeOffForm
    template_name = 'appointments/timeoff_form.html'
    
    def test_func(self):
        # Only the doctor himself, receptionists and admins can add
        user = self.request.user
        doctor_id = self.kwargs.get('doctor_id')
        
        if user.is_doctor():
            return str(user.id) == str(doctor_id)
        return user.is_receptionist() or user.is_admin_user()
    
    def get_initial(self):
        initial = super().get_initial()
        doctor_id = self.kwargs.get('doctor_id')
        if doctor_id:
            initial['doctor'] = doctor_id
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor_id = self.kwargs.get('doctor_id')
        context['doctor'] = get_object_or_404(User, id=doctor_id)
        context['title'] = _('Add New Time Off Day')
        return context
    
    def get_success_url(self):
        return reverse_lazy('doctor-timeoff-list', kwargs={'doctor_id': self.kwargs.get('doctor_id')})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Time off day added successfully.'))
        return response

class DoctorTimeOffUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Doctor time off day update view.
    """
    model = DoctorTimeOff
    form_class = DoctorTimeOffForm
    template_name = 'appointments/timeoff_form.html'
    
    def test_func(self):
        # Only the doctor himself, receptionists and admins can update
        user = self.request.user
        timeoff = self.get_object()
        
        if user.is_doctor():
            return str(user.id) == str(timeoff.doctor.id)
        return user.is_receptionist() or user.is_admin_user()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctor'] = self.object.doctor
        context['title'] = _('Edit Time Off Day')
        return context
    
    def get_success_url(self):
        return reverse_lazy('doctor-timeoff-list', kwargs={'doctor_id': self.object.doctor.id})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Time off day updated successfully.'))
        return response

class DoctorTimeOffDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Doctor time off day deletion view.
    """
    model = DoctorTimeOff
    template_name = 'appointments/timeoff_confirm_delete.html'
    
    def test_func(self):
        # Only the doctor himself, receptionists and admins can delete
        user = self.request.user
        timeoff = self.get_object()
        
        if user.is_doctor():
            return str(user.id) == str(timeoff.doctor.id)
        return user.is_receptionist() or user.is_admin_user()
    
    def get_success_url(self):
        return reverse_lazy('doctor-timeoff-list', kwargs={'doctor_id': self.object.doctor.id})
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, _('Time off day deleted successfully.'))
        return response
