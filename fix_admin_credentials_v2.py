#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')

# Setup Django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

def fix_admin_credentials():
    try:
        # Try to get existing admin user
        admin_user = User.objects.get(username='admin')
        print(f"Found existing admin user: {admin_user.username}")
        
        # Update password to admin123
        admin_user.set_password('admin123')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        print("✅ Admin password updated to 'admin123'")
        
    except User.DoesNotExist:
        # Create new admin user
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@laso-healthcare.com',
            password='admin123'
        )
        print("✅ New admin user created with username 'admin' and password 'admin123'")
    
    # Verify the credentials work
    user = authenticate(username='admin', password='admin123')
    if user:
        print("✅ Admin credentials verified successfully!")
        print("Username: admin")
        print("Password: admin123")
        print(f"Access URL: http://65.108.91.110:3000/admin")
        print(f"Login URL: http://65.108.91.110:3000/login")
    else:
        print("❌ Failed to verify admin credentials")

if __name__ == '__main__':
    fix_admin_credentials()
