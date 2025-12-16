import os
from pathlib import Path

import sys

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'unsafe-secret-for-dev')

DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Simple throttling middleware (can be replaced with django-ratelimit or DRF throttling)
    'core.middleware.SimpleRateLimitMiddleware',
]

ROOT_URLCONF = 'usovs.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'usovs.wsgi.application'

# Use SQLite for test runs when Postgres isn't available (local convenience).
# Set environment variable DJANGO_USE_SQLITE_FOR_TESTS=1 or run tests (`manage.py test`) and
# the code will use SQLite instead of Postgres for the test database.
if 'test' in sys.argv or os.environ.get('DJANGO_USE_SQLITE_FOR_TESTS') == '1':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'test_sqlite.db'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'usovs_db'),
            'USER': os.environ.get('POSTGRES_USER', 'usovs_user'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'password'),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
]

AUTH_USER_MODEL = 'core.User'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Firebase
FIREBASE_CREDENTIALS_JSON = os.environ.get('FIREBASE_CREDENTIALS_JSON')
FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY')
FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN')

# Verification hardening defaults
FIREBASE_VERIFICATION_MAX_ATTEMPTS_PER_IP = int(os.environ.get('FIREBASE_VERIFICATION_MAX_ATTEMPTS_PER_IP', '10'))
FIREBASE_VERIFICATION_WINDOW_SECONDS = int(os.environ.get('FIREBASE_VERIFICATION_WINDOW_SECONDS', '3600'))
# Maximum acceptable token age (seconds) for verification (default 10 minutes)
FIREBASE_TOKEN_MAX_AGE_SECONDS = int(os.environ.get('FIREBASE_TOKEN_MAX_AGE_SECONDS', '600'))

# Logging: simple console for now
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        }
,    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
