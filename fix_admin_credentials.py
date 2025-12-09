#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/root/laso-wise')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')

# Setup Django
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

def fix_admin_credentials():
    try:
        # Try to get existing admin user
        admin_user = User.objects.get(username='admin')
        print(f"Found existing admin user: {admin_user.username}")
        
        # Update password to admin123
        admin_user.set_password('admin123')
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
    from django.contrib.auth import authenticate
    user = authenticate(username='admin', password='admin123')
    if user:
        print("✅ Admin credentials verified successfully!")
        print("Username: admin")
        print("Password: admin123")
        print(f"Access URL: http://65.108.91.110:3000/admin")
    else:
        print("❌ Failed to verify admin credentials")

if __name__ == '__main__':
    fix_admin_credentials()
