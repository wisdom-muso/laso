#!/usr/bin/env python
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from users.models import User

def test_telemedicine_access():
    client = Client()
    
    # Test without login
    print("Testing telemedicine access without login...")
    response = client.get('/telemedicine/')
    print(f"Status: {response.status_code}")
    print(f"Redirect URL: {response.get('Location', 'No redirect')}")
    
    # Test with login
    print("\nTesting telemedicine access with doctor login...")
    user = User.objects.get(username='testdoctor')
    client.force_login(user)
    
    response = client.get('/telemedicine/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: Telemedicine page loaded successfully!")
        print(f"Template used: {response.templates[0].name if response.templates else 'Unknown'}")
    else:
        print(f"ERROR: Status {response.status_code}")
        if hasattr(response, 'content'):
            print(f"Content preview: {response.content[:500].decode()}")

if __name__ == '__main__':
    test_telemedicine_access()
