"""
Test settings for Neravu backend.
Automated tests are isolated from production databases and external networks.
"""

import os
import urllib.parse
import dj_database_url
from .base import *

DEBUG = False
SECRET_KEY = 'neravu-isolated-test-secret-key-for-automated-pytest-runs'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

neon_db_url = os.environ.get('NEON_DATABASE_URL')

if neon_db_url:
    parsed_url = urllib.parse.urlparse(neon_db_url)
    
    # Strictly construct isolated test DB URL targeting 'neravu_test_isolated'
    test_db_url = urllib.parse.urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        '/neravu_test_isolated',
        parsed_url.params,
        parsed_url.query,
        parsed_url.fragment
    ))
    
    DATABASES = {
        'default': dj_database_url.parse(
            test_db_url,
            conn_max_age=0,
            ssl_require=True
        )
    }
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS']['sslmode'] = 'require'
    DATABASES['default']['OPTIONS']['application_name'] = 'neravu_test_runner'
    DATABASES['default']['TEST'] = {
        'NAME': 'neravu_test_isolated',
        'CREATE_DB': False,
    }
else:
    # Isolated local database
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'neravu_test_isolated',
            'USER': 'test_user',
            'PASSWORD': 'test_password',
            'HOST': 'localhost',
            'PORT': '5432',
            'TEST': {
                'NAME': 'neravu_test_isolated',
                'CREATE_DB': False,
            }
        }
    }

# Fail-closed safety assertions:
assert DATABASES['default']['NAME'] == 'neravu_test_isolated', (
    f"Critical Isolation Error: Test settings must target 'neravu_test_isolated', got '{DATABASES['default']['NAME']}'"
)
assert 'production' not in DATABASES['default']['NAME'].lower(), (
    "Critical Security Halt: Test suite attempted to connect to a production database!"
)
assert DATABASES['default']['NAME'] != 'neravu_dev', (
    "Critical Isolation Halt: Test suite must NEVER target the development database 'neravu_dev'!"
)

# Faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Ensure email/SMS does not leave machine during tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
SMS_BACKEND = 'apps.core.sms.MockTestSMSBackend'
