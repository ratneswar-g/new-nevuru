"""
Root URL configuration for Neravu backend.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'service': 'neravu-backend',
        'version': '0.1.0'
    })

urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('admin/', admin.site.urls),
]
