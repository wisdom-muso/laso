from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

@csrf_exempt
@require_POST
def test_admin_login(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user and (user.is_staff or user.is_superuser):
            login(request, user)
            return JsonResponse({
                'success': True,
                'message': f'Login successful for {user.username}',
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials or insufficient permissions'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
