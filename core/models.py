from django.db import models

# İstatistik ve iletişim modelleri buraya import edilecek
# Ancak circular import sorunlarını önlemek için burada import etmiyoruz
from core.models_theme import UserThemePreference
from core.models_sessions import LoginSession

# Enterprise Healthcare Features
from core.models_bed_management import Ward, Room, Bed
from core.models_adt import PatientAdmission, PatientTransfer, VisitType
from core.models_soap_notes import SOAPNote
from core.models_organization import Hospital, Department
