"""
Admin configuration for Enterprise Healthcare Features
Includes Bed Management, ADT, and SOAP Notes
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models_bed_management import Ward, Room, Bed
from .models_adt import PatientAdmission, PatientTransfer, VisitType
from .models_soap_notes import SOAPNote


# ===================================
# Bed Management Admin
# ===================================

@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ('name', 'ward_type', 'floor', 'building', 'total_beds', 'available_beds', 'occupancy_rate_display', 'is_active')
    list_filter = ('ward_type', 'floor', 'is_active')
    search_fields = ('name', 'building', 'description')
    ordering = ['floor', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'ward_type', 'floor', 'building')
        }),
        (_('Details'), {
            'fields': ('description', 'head_nurse', 'is_active')
        }),
    )
    
    def occupancy_rate_display(self, obj):
        rate = obj.occupancy_rate
        if rate >= 90:
            color = 'red'
        elif rate >= 70:
            color = 'orange'
        else:
            color = 'green'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)
    occupancy_rate_display.short_description = _('Occupancy Rate')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'ward', 'room_type', 'capacity', 'available_beds', 'daily_rate', 'is_active')
    list_filter = ('ward', 'room_type', 'is_active', 'has_bathroom', 'has_tv', 'has_ac')
    search_fields = ('room_number', 'ward__name', 'notes')
    ordering = ['ward', 'room_number']
    
    fieldsets = (
        (None, {
            'fields': ('ward', 'room_number', 'room_type', 'capacity')
        }),
        (_('Amenities'), {
            'fields': ('has_bathroom', 'has_tv', 'has_ac')
        }),
        (_('Pricing'), {
            'fields': ('daily_rate',)
        }),
        (_('Notes'), {
            'fields': ('notes', 'is_active'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('bed_number', 'room', 'bed_type', 'status_display', 'current_patient', 'has_monitor', 'last_cleaned', 'is_active')
    list_filter = ('status', 'bed_type', 'room__ward', 'is_active', 'has_oxygen', 'has_suction', 'has_monitor')
    search_fields = ('bed_number', 'room__room_number', 'room__ward__name', 'current_patient__username', 'current_patient__first_name')
    ordering = ['room__ward', 'room', 'bed_number']
    raw_id_fields = ('current_patient',)
    
    fieldsets = (
        (None, {
            'fields': ('room', 'bed_number', 'bed_type', 'status')
        }),
        (_('Patient'), {
            'fields': ('current_patient',)
        }),
        (_('Equipment'), {
            'fields': ('has_oxygen', 'has_suction', 'has_monitor')
        }),
        (_('Maintenance'), {
            'fields': ('notes', 'last_cleaned', 'is_active')
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'available': 'green',
            'occupied': 'red',
            'reserved': 'orange',
            'maintenance': 'gray',
            'cleaning': 'blue'
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())
    status_display.short_description = _('Status')


# ===================================
# ADT (Admission/Discharge/Transfer) Admin
# ===================================

@admin.register(PatientAdmission)
class PatientAdmissionAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'patient', 'admission_type', 'status_display', 'admitting_doctor', 'bed', 'admission_date', 'length_of_stay')
    list_filter = ('status', 'admission_type', 'payment_type', 'admission_date')
    search_fields = ('admission_number', 'patient__username', 'patient__first_name', 'patient__last_name', 'admission_diagnosis')
    date_hierarchy = 'admission_date'
    raw_id_fields = ('patient', 'admitting_doctor', 'attending_doctor', 'discharged_by', 'bed')
    ordering = ['-admission_date']
    
    fieldsets = (
        (_('Admission Information'), {
            'fields': ('admission_number', 'patient', 'admission_type', 'status', 'admission_date')
        }),
        (_('Medical Information'), {
            'fields': ('admitting_doctor', 'attending_doctor', 'admission_diagnosis', 'chief_complaint')
        }),
        (_('Bed Assignment'), {
            'fields': ('bed',)
        }),
        (_('Dates'), {
            'fields': ('expected_discharge_date', 'actual_discharge_date')
        }),
        (_('Emergency Contact'), {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'),
            'classes': ('collapse',)
        }),
        (_('Payment'), {
            'fields': ('payment_type', 'insurance_policy_number'),
            'classes': ('collapse',)
        }),
        (_('Discharge Information'), {
            'fields': ('discharge_diagnosis', 'discharge_summary', 'discharge_instructions', 'follow_up_instructions', 'discharged_by'),
            'classes': ('collapse',)
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'admitted': 'blue',
            'in_treatment': 'orange',
            'pending_discharge': 'purple',
            'discharged': 'green',
            'transferred': 'gray',
            'deceased': 'black',
            'absconded': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())
    status_display.short_description = _('Status')


@admin.register(PatientTransfer)
class PatientTransferAdmin(admin.ModelAdmin):
    list_display = ('admission', 'from_bed', 'to_bed', 'transfer_reason', 'transferred_by', 'transfer_date')
    list_filter = ('transfer_reason', 'transfer_date')
    search_fields = ('admission__patient__first_name', 'admission__patient__last_name', 'admission__admission_number')
    date_hierarchy = 'transfer_date'
    raw_id_fields = ('admission', 'from_bed', 'to_bed', 'transferred_by')


@admin.register(VisitType)
class VisitTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'default_duration_minutes', 'requires_admission', 'is_active')
    list_filter = ('category', 'requires_admission', 'is_active')
    search_fields = ('name', 'description')


# ===================================
# SOAP Notes Admin
# ===================================

@admin.register(SOAPNote)
class SOAPNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'provider', 'encounter_type', 'encounter_date', 'primary_diagnosis', 'status_display')
    list_filter = ('status', 'encounter_type', 'encounter_date', 'provider')
    search_fields = ('patient__first_name', 'patient__last_name', 'primary_diagnosis', 'chief_complaint')
    date_hierarchy = 'encounter_date'
    raw_id_fields = ('patient', 'provider', 'appointment', 'admission', 'co_signed_by')
    readonly_fields = ('signed_at', 'created_at', 'updated_at')
    ordering = ['-encounter_date']
    
    fieldsets = (
        (_('Encounter Information'), {
            'fields': ('patient', 'provider', 'appointment', 'admission', 'encounter_date', 'encounter_type', 'status')
        }),
        (_('Chief Complaint'), {
            'fields': ('chief_complaint',)
        }),
        (_('SUBJECTIVE'), {
            'fields': ('history_of_present_illness', 'symptom_onset', 'symptom_duration', 'symptom_severity',
                      'aggravating_factors', 'alleviating_factors', 'past_medical_history', 
                      'medications_at_home', 'allergies', 'family_history', 'social_history', 'review_of_systems'),
            'classes': ('collapse',)
        }),
        (_('OBJECTIVE'), {
            'fields': ('vital_signs_summary', 'general_appearance', 'physical_examination',
                      'heent_exam', 'cardiovascular_exam', 'respiratory_exam', 'abdominal_exam',
                      'neurological_exam', 'musculoskeletal_exam', 'skin_exam', 'psychiatric_exam',
                      'lab_results', 'imaging_results', 'other_diagnostic_results'),
            'classes': ('collapse',)
        }),
        (_('ASSESSMENT'), {
            'fields': ('primary_diagnosis', 'primary_diagnosis_icd10', 'secondary_diagnoses',
                      'differential_diagnoses', 'clinical_impression', 'prognosis')
        }),
        (_('PLAN'), {
            'fields': ('treatment_plan', 'medications_prescribed', 'procedures_performed',
                      'procedures_ordered', 'labs_ordered', 'imaging_ordered', 'referrals',
                      'patient_education', 'lifestyle_modifications', 'follow_up_instructions',
                      'follow_up_timeframe', 'return_precautions')
        }),
        (_('Signature'), {
            'fields': ('time_spent_minutes', 'signed_at', 'co_signed_by', 'amendment_notes'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'draft': 'orange',
            'completed': 'blue',
            'amended': 'purple',
            'signed': 'green'
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())
    status_display.short_description = _('Status')
