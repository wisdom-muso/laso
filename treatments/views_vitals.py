"""
Views for Vital Signs Management
Handles CRUD operations, real-time updates, and role-based access control
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Q, Avg, Max, Min
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models_vitals import VitalSign, VitalSignAlert
from .forms_vitals import VitalSignForm, VitalSignFilterForm
from .serializers_vitals import VitalSignSerializer, VitalSignAlertSerializer
from core.models_notifications import Notification
from django.contrib.auth import get_user_model

User = get_user_model()


class VitalSignPermissionMixin:
    """Mixin to handle vital sign permissions"""
    
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_doctor() or user.is_admin_user())
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user():
            return VitalSign.objects.all()
        elif user.is_doctor():
            # Doctors can see vitals of their patients
            return VitalSign.objects.filter(
                Q(patient__doctor_appointments__doctor=user) |
                Q(recorded_by=user)
            ).distinct()
        elif user.is_patient():
            # Patients can only see their own vitals
            return VitalSign.objects.filter(patient=user)
        return VitalSign.objects.none()


class VitalSignListView(LoginRequiredMixin, VitalSignPermissionMixin, ListView):
    """List view for vital signs with filtering and pagination"""
    model = VitalSign
    template_name = 'treatments/vitals_list.html'
    context_object_name = 'vitals'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        patient_id = self.request.GET.get('patient')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        risk_level = self.request.GET.get('risk_level')
        
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(recorded_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(recorded_at__date__lte=date_to)
            except ValueError:
                pass
        
        if risk_level:
            queryset = queryset.filter(overall_risk_level=risk_level)
        
        return queryset.select_related('patient', 'recorded_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = VitalSignFilterForm(self.request.GET)
        
        # Add statistics
        queryset = self.get_queryset()
        context['total_records'] = queryset.count()
        context['high_risk_count'] = queryset.filter(
            overall_risk_level__in=['high', 'critical']
        ).count()
        
        return context


class VitalSignDetailView(LoginRequiredMixin, VitalSignPermissionMixin, DetailView):
    """Detail view for a single vital sign record"""
    model = VitalSign
    template_name = 'treatments/vitals_detail.html'
    context_object_name = 'vital'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vital = self.get_object()
        
        # Get recent vitals for comparison
        recent_vitals = VitalSign.objects.filter(
            patient=vital.patient,
            recorded_at__lt=vital.recorded_at
        ).order_by('-recorded_at')[:5]
        
        context['recent_vitals'] = recent_vitals
        context['alerts'] = vital.alerts.all()
        
        return context


class VitalSignCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create view for new vital sign records"""
    model = VitalSign
    form_class = VitalSignForm
    template_name = 'treatments/vitals_form.html'
    
    def test_func(self):
        return self.request.user.is_doctor() or self.request.user.is_admin_user()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        response = super().form_valid(form)
        
        # Check for alerts after saving
        self.check_and_create_alerts(form.instance)
        
        messages.success(
            self.request,
            f'Vital signs recorded successfully for {form.instance.patient}'
        )
        return response
    
    def get_success_url(self):
        return reverse('treatments:vitals_detail', kwargs={'pk': self.object.pk})
    
    def check_and_create_alerts(self, vital_sign):
        """Check vital signs and create alerts if necessary"""
        alerts_created = []
        
        # Blood pressure alerts
        if vital_sign.bp_category in ['stage2', 'crisis']:
            alert = VitalSignAlert.objects.create(
                vital_sign=vital_sign,
                alert_type='high_bp',
                severity='critical' if vital_sign.bp_category == 'crisis' else 'high',
                message=f'Critical blood pressure reading: {vital_sign.blood_pressure_display} mmHg'
            )
            alerts_created.append(alert)
        
        # Heart rate alerts
        if vital_sign.heart_rate > 120:
            alert = VitalSignAlert.objects.create(
                vital_sign=vital_sign,
                alert_type='high_hr',
                severity='high',
                message=f'High heart rate: {vital_sign.heart_rate} bpm'
            )
            alerts_created.append(alert)
        elif vital_sign.heart_rate < 50:
            alert = VitalSignAlert.objects.create(
                vital_sign=vital_sign,
                alert_type='low_hr',
                severity='high',
                message=f'Low heart rate: {vital_sign.heart_rate} bpm'
            )
            alerts_created.append(alert)
        
        # Temperature alerts
        if vital_sign.temperature:
            if vital_sign.temperature > 38.5:
                alert = VitalSignAlert.objects.create(
                    vital_sign=vital_sign,
                    alert_type='high_temp',
                    severity='elevated',
                    message=f'High temperature: {vital_sign.temperature}°C'
                )
                alerts_created.append(alert)
        
        # Oxygen saturation alerts
        if vital_sign.oxygen_saturation and vital_sign.oxygen_saturation < 90:
            alert = VitalSignAlert.objects.create(
                vital_sign=vital_sign,
                alert_type='low_o2',
                severity='critical',
                message=f'Low oxygen saturation: {vital_sign.oxygen_saturation}%'
            )
            alerts_created.append(alert)
        
        # Send notifications for created alerts
        for alert in alerts_created:
            self.send_alert_notifications(alert)
    
    def send_alert_notifications(self, alert):
        """Send notifications to relevant users for alerts"""
        # Get patient's doctors
        patient = alert.vital_sign.patient
        doctors = User.objects.filter(
            user_type='doctor',
            doctor_appointments__patient=patient
        ).distinct()
        
        # Get super admins
        super_admins = User.objects.filter(user_type='admin')
        
        # Combine recipients
        recipients = list(doctors) + list(super_admins)
        
        for recipient in recipients:
            Notification.objects.create(
                user=recipient,
                title=f'Vital Sign Alert: {patient.get_full_name()}',
                message=alert.message,
                notification_type='vital_alert',
                priority='high' if alert.severity in ['high', 'critical'] else 'medium'
            )
            alert.notified_users.add(recipient)


class VitalSignUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update view for vital sign records"""
    model = VitalSign
    form_class = VitalSignForm
    template_name = 'treatments/vitals_form.html'
    
    def test_func(self):
        vital = self.get_object()
        user = self.request.user
        return (user.is_doctor() or user.is_admin_user()) and \
               (vital.recorded_by == user or user.is_admin_user())
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Vital signs updated successfully')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('treatments:vitals_detail', kwargs={'pk': self.object.pk})


@login_required
def patient_vitals_dashboard(request, patient_id=None):
    """Dashboard view for patient vitals"""
    if patient_id:
        # Doctor/Admin viewing specific patient
        if not (request.user.is_doctor() or request.user.is_admin_user()):
            return HttpResponseForbidden()
        patient = get_object_or_404(User, id=patient_id, user_type='patient')
    else:
        # Patient viewing their own vitals
        if not request.user.is_patient():
            return HttpResponseForbidden()
        patient = request.user
    
    # Get latest vitals
    latest_vital = VitalSign.objects.filter(patient=patient).first()
    
    # Get vitals history (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_vitals = VitalSign.objects.filter(
        patient=patient,
        recorded_at__gte=thirty_days_ago
    ).order_by('-recorded_at')
    
    # Calculate averages for the period
    vitals_stats = recent_vitals.aggregate(
        avg_systolic=Avg('systolic_bp'),
        avg_diastolic=Avg('diastolic_bp'),
        avg_heart_rate=Avg('heart_rate'),
        max_systolic=Max('systolic_bp'),
        min_systolic=Min('systolic_bp'),
    )
    
    # Get active alerts
    active_alerts = VitalSignAlert.objects.filter(
        vital_sign__patient=patient,
        status='active'
    ).order_by('-created_at')
    
    # Prepare chart data
    chart_data = {
        'dates': [v.recorded_at.strftime('%Y-%m-%d') for v in recent_vitals[:10]],
        'systolic': [v.systolic_bp for v in recent_vitals[:10]],
        'diastolic': [v.diastolic_bp for v in recent_vitals[:10]],
        'heart_rate': [v.heart_rate for v in recent_vitals[:10]],
    }
    
    context = {
        'patient': patient,
        'latest_vital': latest_vital,
        'recent_vitals': recent_vitals[:10],
        'vitals_stats': vitals_stats,
        'active_alerts': active_alerts,
        'chart_data': chart_data,
        'is_own_dashboard': patient == request.user,
    }
    
    return render(request, 'treatments/patient_vitals_dashboard.html', context)


@login_required
def vitals_api_latest(request, patient_id):
    """API endpoint to get latest vitals for a patient"""
    if not (request.user.is_doctor() or request.user.is_admin_user() or 
            (request.user.is_patient() and request.user.id == int(patient_id))):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        patient = User.objects.get(id=patient_id, user_type='patient')
        latest_vital = VitalSign.objects.filter(patient=patient).first()
        
        if latest_vital:
            data = {
                'id': latest_vital.id,
                'systolic_bp': latest_vital.systolic_bp,
                'diastolic_bp': latest_vital.diastolic_bp,
                'heart_rate': latest_vital.heart_rate,
                'temperature': float(latest_vital.temperature) if latest_vital.temperature else None,
                'oxygen_saturation': latest_vital.oxygen_saturation,
                'cholesterol_total': latest_vital.cholesterol_total,
                'blood_glucose': latest_vital.blood_glucose,
                'overall_risk_level': latest_vital.overall_risk_level,
                'bp_category': latest_vital.bp_category,
                'recorded_at': latest_vital.recorded_at.isoformat(),
                'bmi': latest_vital.bmi,
            }
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'No vitals found'}, status=404)
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)


# REST API ViewSets for mobile/API access
class VitalSignViewSet(viewsets.ModelViewSet):
    """REST API ViewSet for VitalSign model"""
    serializer_class = VitalSignSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user():
            return VitalSign.objects.all()
        elif user.is_doctor():
            return VitalSign.objects.filter(
                Q(patient__doctor_appointments__doctor=user) |
                Q(recorded_by=user)
            ).distinct()
        elif user.is_patient():
            return VitalSign.objects.filter(patient=user)
        return VitalSign.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def latest_by_patient(self, request):
        """Get latest vitals for each patient"""
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            try:
                patient = User.objects.get(id=patient_id, user_type='patient')
                latest = VitalSign.objects.filter(patient=patient).first()
                if latest:
                    serializer = self.get_serializer(latest)
                    return Response(serializer.data)
                return Response({'error': 'No vitals found'}, status=404)
            except User.DoesNotExist:
                return Response({'error': 'Patient not found'}, status=404)
        
        return Response({'error': 'patient_id parameter required'}, status=400)


class VitalSignAlertViewSet(viewsets.ModelViewSet):
    """REST API ViewSet for VitalSignAlert model"""
    serializer_class = VitalSignAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user():
            return VitalSignAlert.objects.all()
        elif user.is_doctor():
            return VitalSignAlert.objects.filter(
                vital_sign__patient__doctor_appointments__doctor=user
            ).distinct()
        elif user.is_patient():
            return VitalSignAlert.objects.filter(vital_sign__patient=user)
        return VitalSignAlert.objects.none()
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert"""
        alert = self.get_object()
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        return Response({'status': 'acknowledged'})

@login_required
def realtime_vitals_dashboard(request, patient_id=None):
    """
    Real-time vitals dashboard with WebSocket integration
    """
    user = request.user
    
    if patient_id:
        # Viewing another patient's vitals (doctors/admins only)
        if not (user.is_doctor() or user.is_admin_user()):
            messages.error(request, 'You do not have permission to view this patient\'s vitals.')
            return redirect('dashboard')
        
        try:
            patient = User.objects.get(id=patient_id, user_type='patient')
            
            # Check if doctor has treated this patient
            if user.is_doctor():
                from appointments.models import Appointment
                has_appointment = Appointment.objects.filter(
                    doctor=user, patient=patient
                ).exists()
                
                if not has_appointment:
                    messages.error(request, 'You do not have permission to view this patient\'s vitals.')
                    return redirect('dashboard')
            
            is_own_dashboard = False
        except User.DoesNotExist:
            messages.error(request, 'Patient not found.')
            return redirect('dashboard')
    else:
        # Viewing own vitals
        if not user.is_patient():
            messages.error(request, 'Only patients can view their own vitals dashboard.')
            return redirect('dashboard')
        
        patient = user
        is_own_dashboard = True
    
    # Get latest vitals for initial display
    latest_vital = VitalSign.objects.filter(patient=patient).first()
    
    context = {
        'patient': patient,
        'is_own_dashboard': is_own_dashboard,
        'latest_vital': latest_vital,
    }
    
    return render(request, 'treatments/realtime_vitals_dashboard.html', context)

@login_required
def realtime_vitals_dashboard(request, patient_id=None):
    """
    Real-time vitals dashboard with WebSocket support for live updates
    """
    user = request.user
    
    if patient_id:
        # Viewing another patient's vitals (doctors/admins only)
        if not (user.is_doctor() or user.is_admin_user()):
            messages.error(request, 'You do not have permission to view this patient\'s vitals.')
            return redirect('dashboard')
        
        try:
            patient = User.objects.get(id=patient_id, user_type='patient')
            is_own_dashboard = False
            
            # Verify doctor has access to this patient
            if user.is_doctor():
                from appointments.models import Appointment
                has_access = Appointment.objects.filter(
                    doctor=user,
                    patient=patient
                ).exists()
                
                if not has_access:
                    messages.error(request, 'You do not have access to this patient\'s vitals.')
                    return redirect('dashboard')
                    
        except User.DoesNotExist:
            messages.error(request, 'Patient not found.')
            return redirect('dashboard')
    else:
        # Viewing own vitals
        if not user.is_patient():
            messages.error(request, 'Only patients can view their own vitals dashboard.')
            return redirect('dashboard')
        
        patient = user
        is_own_dashboard = True
    
    # Get latest vitals for initial display
    from treatments.models_vitals import VitalSign
    latest_vital = VitalSign.objects.filter(patient=patient).order_by('-recorded_at').first()
    
    # Get recent vitals history for chart display
    recent_vitals = VitalSign.objects.filter(
        patient=patient
    ).order_by('-recorded_at')[:10]
    
    context = {
        'patient': patient,
        'is_own_dashboard': is_own_dashboard,
        'latest_vital': latest_vital,
        'recent_vitals': recent_vitals,
        'patient_id': patient.id,
        'websocket_url': f'ws/vitals/{"doctor/" + str(patient.id) + "/" if not is_own_dashboard else ""}',
    }
    
    return render(request, 'treatments/realtime_vitals_dashboard.html', context)