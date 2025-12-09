from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models_availability import DoctorAvailability, DoctorTimeOff

User = get_user_model()

class DoctorAvailabilityForm(forms.ModelForm):
    """
    Doctor working hours form.
    """
    class Meta:
        model = DoctorAvailability
        fields = ['doctor', 'weekday', 'start_time', 'end_time', 'is_active']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'weekday': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only users of type doctor
        self.fields['doctor'].queryset = User.objects.filter(user_type='doctor')
        
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(_('Start time must be before end time.'))
        
        return cleaned_data

class DoctorTimeOffForm(forms.ModelForm):
    """
    Doctor leave days form.
    """
    class Meta:
        model = DoctorTimeOff
        fields = ['doctor', 'start_date', 'end_date', 'start_time', 'end_time', 'reason', 'is_full_day']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            'is_full_day': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only users of type doctor
        self.fields['doctor'].queryset = User.objects.filter(user_type='doctor')
        
        # Optional fields
        self.fields['reason'].required = False
        self.fields['start_time'].required = False
        self.fields['end_time'].required = False
        
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_full_day = cleaned_data.get('is_full_day')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(_('Start date must be before end date.'))
        
        if not is_full_day:
            if not start_time:
                self.add_error('start_time', _('Start time is required if not a full day off.'))
            if not end_time:
                self.add_error('end_time', _('End time is required if not a full day off.'))
            elif start_time and end_time and start_time >= end_time:
                raise forms.ValidationError(_('Start time must be before end time.'))
        
        return cleaned_data
