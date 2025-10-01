"""
Local development settings for dnd_character_creator project.
"""
from .base import *

# Override for local development
DEBUG = True

# For local development, use SQLite if no PostgreSQL is available
import os
if not os.getenv('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Allow all hosts in local development
ALLOWED_HOSTS = ['*']

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug toolbar for development
if 'django_debug_toolbar' in [app for app_list in [DJANGO_APPS, THIRD_PARTY_APPS, LOCAL_APPS] for app in app_list]:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Disable caching in development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# More lenient CORS for development
CORS_ALLOW_ALL_ORIGINS = True

# Login URL for @login_required decorator
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/characters/'