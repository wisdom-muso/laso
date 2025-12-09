import os
import django
from django.contrib.auth import get_user_model
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()

from core.models_organization import Hospital, Department
from core.models_bed_management import Ward, Room, Bed

User = get_user_model()

def setup_data():
    print("Setting up test data...")
    
    # 1. Create Hospital
    hospital, created = Hospital.objects.get_or_create(
        slug='general-hospital',
        defaults={
            'name': 'General Hospital',
            'email': 'admin@generalhospital.com',
            'phone_number': '555-0199',
            'subscription_plan': 'enterprise'
        }
    )
    if created:
        print(f"Created Hospital: {hospital.name}")
    else:
        print(f"Using existing Hospital: {hospital.name}")

    # 2. Create Department
    dept, created = Department.objects.get_or_create(
        hospital=hospital,
        name='Internal Medicine',
        defaults={'description': 'General internal medicine'}
    )

    # 3. Create Doctor User
    email = 'doctor@test.com'
    if not User.objects.filter(email=email).exists():
        doctor = User.objects.create_user(
            username='dr_test',
            email=email,
            password='password123',
            user_type='doctor',
            first_name='Test',
            last_name='Doctor',
            hospital=hospital,
            department=dept
        )
        print(f"Created Doctor User: {doctor.username} (password123)")
    else:
        doctor = User.objects.get(email=email)
        # Ensure correct password
        doctor.set_password('password123')
        doctor.hospital = hospital
        doctor.department = dept
        doctor.save()
        print(f"Updated Doctor User: {doctor.username}")

    # 4. Create Patient User
    p_email = 'patient@test.com'
    if not User.objects.filter(email=p_email).exists():
        patient = User.objects.create_user(
            username='patient_test',
            email=p_email,
            password='password123',
            user_type='patient',
            first_name='John',
            last_name='Doe',
            hospital=hospital
        )
        print(f"Created Patient User: {patient.username}")
    else:
        patient = User.objects.get(email=p_email)
        patient.hospital = hospital
        patient.save()
        print(f"Patient User exists: {patient.username}")

    # 5. Create Ward/Bed if missing
    ward, created = Ward.objects.get_or_create(
        name='Ward A',
        defaults={'ward_type': 'general', 'floor': 1}
    )
    
    if created or not Room.objects.filter(ward=ward).exists():
        room = Room.objects.create(ward=ward, room_number='101', room_type='semiprivate')
        Bed.objects.create(room=room, bed_number='101-A', bed_type='standard')
        Bed.objects.create(room=room, bed_number='101-B', bed_type='standard')
        print("Created Ward A with Room 101 and 2 Beds")

    print("Test data setup complete.")

if __name__ == '__main__':
    setup_data()
