from django.urls import re_path
from . import vitals_consumers

websocket_urlpatterns = [
    re_path(r'ws/vitals/$', vitals_consumers.VitalsConsumer.as_asgi()),
    re_path(r'ws/vitals/doctor/(?P<patient_id>\d+)/$', vitals_consumers.DoctorVitalsConsumer.as_asgi()),
]