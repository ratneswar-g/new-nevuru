"""
Local development settings for Neravu backend.
"""

import os
import urllib.parse
import dj_database_url
from .base import *

DEBUG = True
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'neravu-dev-secret-key-not-for-production-usage-only')

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Authoritative Database: Neon Managed PostgreSQL (or local fallback)
neon_db_url = os.environ.get('NEON_DATABASE_URL')

if neon_db_url:
    parsed_neon = urllib.parse.urlparse(neon_db_url)
    db_target_name = parsed_neon.path.lstrip('/')
    
    # Fail-closed safety assertion against production targets
    assert 'production' not in db_target_name.lower() and 'prod' not in db_target_name.lower().split('_'), (
        f"Critical Safety Error: Development settings cannot target production database: '{db_target_name}'"
    )
    
    DATABASES = {
        'default': dj_database_url.parse(
            neon_db_url,
            conn_max_age=600,
            ssl_require=True,
        )
    }
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS']['sslmode'] = 'require'
    DATABASES['default']['OPTIONS']['application_name'] = 'neravu_local_dev'
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'neravu_dev'),
            'USER': os.environ.get('POSTGRES_USER', 'neravu_user'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'neravu_password'),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }

# CORS Configuration for local client applications
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # AI Studio Dev / Root Vite
    'http://localhost:5173',  # Website
    'http://localhost:5174',  # Admin Dashboard
    'http://localhost:8081',  # Expo Metro Bundler
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:5174',
    'http://127.0.0.1:8081',
]

CORS_ALLOW_CREDENTIALS = True

# Email / SMS / Mock Provider for local development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
SMS_BACKEND = 'apps.core.sms.ConsoleSMSBackend'
