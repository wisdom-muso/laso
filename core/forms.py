from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import datetime

from appointments.models import Appointment
from treatments.models import Treatment, Prescription
from treatments.models_medications import Medication, MedicationInteraction
from treatments.models_medical_history import MedicalHistory
from .models_theme import UserThemePreference

User = get_user_model()

class LoginForm(AuthenticationForm):
    """
    Custom user login form that extends AuthenticationForm.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Username')}),
        label=_('Username')
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Password')}),
        label=_('Password')
    )

class PatientRegistrationForm(UserCreationForm):
    """
    Patient registration form for creating new patient users.
    """
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('First Name')}),
        label=_('First Name')
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Last Name')}),
        label=_('Last Name')
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')}),
        label=_('Email')
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label=_('Date of Birth')
    )
    phone_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Phone Number')}),
        label=_('Phone Number')
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Address')}),
        label=_('Address')
    )
    blood_type = forms.ChoiceField(
        choices=[
            ('', _('Select Blood Type')),
            ('A+', 'A+'),
            ('A-', 'A-'),
            ('B+', 'B+'),
            ('B-', 'B-'),
            ('AB+', 'AB+'),
            ('AB-', 'AB-'),
            ('0+', '0+'),
            ('0-', '0-'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Blood Type'),
        required=False
    )
    
    gender = forms.ChoiceField(
        choices=[
            ('', _('Select Gender')),
            ('M', _('Male')),
            ('F', _('Female')),
            ('O', _('Other')),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Gender'),
        required=False
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 
                 'date_of_birth', 'phone_number', 'address', 'blood_type', 'gender')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': _('Username')})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': _('Password')})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': _('Confirm Password')})
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('A user with this email already exists.'))
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError(_('A user with this username already exists.'))
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'patient'
        if commit:
            user.save()
        return user

class AppointmentForm(forms.ModelForm):
    """
    Appointment creation and editing form.
    """
    class Meta:
        model = Appointment
        fields = ('patient', 'doctor', 'date', 'time', 'description')
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Show only patient type users
        self.fields['patient'].queryset = User.objects.filter(user_type='patient')
        
        # Show only doctor type users
        self.fields['doctor'].queryset = User.objects.filter(user_type='doctor')
        
        # If logged in user is a patient, they can only select themselves
        if user and user.is_patient():
            self.fields['patient'].initial = user
            self.fields['patient'].widget = forms.HiddenInput()
            self.fields['date'].help_text = _('Select the date you want to schedule an appointment')
            self.fields['time'].help_text = _('Select the time you want to schedule an appointment')
            self.fields['description'].help_text = _('Briefly describe the reason for your appointment')
        
        # Add restriction for future appointments
        today = datetime.date.today()
        self.fields['date'].widget.attrs['min'] = today.strftime('%Y-%m-%d')

class TreatmentForm(forms.ModelForm):
    """
    Treatment creation and editing form.
    """
    class Meta:
        model = Treatment
        fields = ('diagnosis', 'notes')
        widgets = {
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PrescriptionForm(forms.ModelForm):
    """
    Prescription creation and editing form.
    """
    medication = forms.ModelChoiceField(
        queryset=Medication.objects.all().order_by('name'),
        label=_('Select Medication from Database'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select select2'}),
        help_text=_('If you select from the medication database, drug interactions will be automatically checked.')
    )
    
    class Meta:
        model = Prescription
        fields = ('medication', 'name', 'dosage', 'instructions')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If instance exists and has medication value, populate name field
        if self.instance and self.instance.pk and self.instance.medication:
            self.fields['name'].initial = self.instance.medication.name
            self.fields['medication'].initial = self.instance.medication
    
    def clean(self):
        cleaned_data = super().clean()
        medication = cleaned_data.get('medication')
        name = cleaned_data.get('name')
        
        # If medication is selected from database, auto-populate medication name
        if medication and not name:
            cleaned_data['name'] = medication.name
        
        return cleaned_data

PrescriptionFormSet = forms.inlineformset_factory(
    Treatment, 
    Prescription, 
    form=PrescriptionForm, 
    extra=1, 
    can_delete=True
)

class DoctorCreationForm(forms.ModelForm):
    """
    Doctor creation form
    """
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Password')}),
        strip=False,
    )
    password2 = forms.CharField(
        label=_('Password (Repeat)'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Password (Repeat)')}),
        strip=False,
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'specialization', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Username')}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('First Name')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Last Name')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Specialization')}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Passwords do not match."))
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.user_type = 'doctor'
        if commit:
            user.save()
        return user

class DoctorUpdateForm(forms.ModelForm):
    """
    Doctor update form
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'specialization', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('First Name')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Last Name')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Specialization')}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Phone')}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Phone number and specialization are not required
        self.fields['phone_number'].required = False
        self.fields['specialization'].required = True
        
class MedicalHistoryForm(forms.ModelForm):
    """
    Patient medical history addition and editing form.
    """
    class Meta:
        model = MedicalHistory
        fields = ['patient', 'condition_type', 'condition_name', 'diagnosed_date', 'notes', 'is_active']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'condition_type': forms.Select(attrs={'class': 'form-control'}),
            'condition_name': forms.TextInput(attrs={'class': 'form-control'}),
            'diagnosed_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only patient type users
        self.fields['patient'].queryset = User.objects.filter(user_type='patient')

class ProfileSettingsForm(forms.ModelForm):
    """
    Profile settings form for updating user profile and preferences.
    """
    theme = forms.ChoiceField(
        choices=UserThemePreference.THEME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Theme Preference'),
        required=False
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('First Name')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Last Name')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Phone Number')}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial theme value if user has theme preference
        if self.instance and hasattr(self.instance, 'theme_preference'):
            self.fields['theme'].initial = self.instance.theme_preference.theme
        else:
            self.fields['theme'].initial = 'light'
    
    def save(self, commit=True):
        user = super().save(commit)
        
        # Save theme preference
        theme = self.cleaned_data.get('theme')
        if theme:
            theme_preference, created = UserThemePreference.objects.get_or_create(user=user)
            theme_preference.theme = theme
            theme_preference.dark_mode = (theme == 'dark')
            theme_preference.save()
        
        return user

class PatientOnboardingForm(forms.ModelForm):
    """
    Form for staff (Receptionist/Doctor) to onboard a new patient.
    Difference from PatientRegistrationForm:
    - No password required (auto-generated)
    - Username auto-generated
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'date_of_birth', 'phone_number', 'gender', 'blood_type', 'address')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('First Name')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Last Name')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email (Optional)')}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Phone Number')}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_type': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False