"""
Django Settings — AI Interview Simulator
"""
import os
import dj_database_url
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ─────────────────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-replace-this-key')
DEBUG      = os.getenv('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS — always include .onrender.com wildcard in production
_raw_hosts = os.getenv('ALLOWED_HOSTS', '').strip()
if _raw_hosts:
    ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['*']

# In production always add the onrender wildcard as safety net
if not DEBUG:
    if not any(h in ('*', '.onrender.com') or 'onrender.com' in h for h in ALLOWED_HOSTS):
        ALLOWED_HOSTS.append('.onrender.com')

# ── Apps ─────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'channels',
    # Local
    'apps.users',
    'apps.interview',
    'apps.resume_screening',
]

# ── Middleware ────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF     = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ── Templates ────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': False,
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

# ── Auth ─────────────────────────────────────────────────────
AUTH_USER_MODEL     = 'users.CustomUser'
LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Database ─────────────────────────────────────────────────
_DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
_SQLITE_DB = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
}

if _DATABASE_URL and _DATABASE_URL.startswith('postgres'):
    try:
        _parsed = dj_database_url.parse(_DATABASE_URL, conn_max_age=600)
        if _parsed and _parsed.get('NAME'):
            DATABASES = {'default': _parsed}
        else:
            DATABASES = {'default': _SQLITE_DB}
    except Exception:
        DATABASES = {'default': _SQLITE_DB}
else:
    DATABASES = {'default': _SQLITE_DB}

# ── REST Framework ───────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '120/minute',
        'token_obtain': '5/minute',
        'token_refresh': '10/minute',
    },
}

# ── JWT ──────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':   timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME':  timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':   True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM':               'HS256',
    'SIGNING_KEY':             SECRET_KEY,
    'AUTH_HEADER_TYPES':       ('Bearer',),
    'AUTH_HEADER_NAME':        'HTTP_AUTHORIZATION',
    'USER_ID_FIELD':           'id',
    'USER_ID_CLAIM':           'user_id',
    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.jwt_utils.CustomTokenObtainPairSerializer',
    'UPDATE_LAST_LOGIN':       True,
}

# ── CORS ─────────────────────────────────────────────────────
_cors_raw = os.getenv('CORS_ALLOWED_ORIGINS', '').strip()
if _cors_raw:
    CORS_ALLOWED_ORIGINS  = [o.strip() for o in _cors_raw.split(',') if o.strip()]
    CORS_ALLOW_ALL_ORIGINS = False
else:
    CORS_ALLOW_ALL_ORIGINS = True   # safe for dev; production sets the env var
CORS_ALLOW_CREDENTIALS = True

# ── Static & Media ───────────────────────────────────────────
STATIC_URL       = '/static/'
STATIC_ROOT      = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Channel Layers ───────────────────────────────────────────
_REDIS_URL = os.getenv('REDIS_URL', '').strip()
if _REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG':  {'hosts': [_REDIS_URL]},
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# ── AI APIs ──────────────────────────────────────────────────
OPENAI_API_KEY    = os.getenv('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# ── i18n ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Production security headers ──────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT     = False   # Render handles HTTPS termination
    SESSION_COOKIE_SECURE   = True
    CSRF_COOKIE_SECURE      = True

    # CSRF_TRUSTED_ORIGINS — start from non-wildcard ALLOWED_HOSTS
    _csrf_hosts = [h for h in ALLOWED_HOSTS if h and '*' not in h]
    CSRF_TRUSTED_ORIGINS = [f'https://{h}' for h in _csrf_hosts]

    # Override with explicit env var if provided
    _csrf_env = os.getenv('CSRF_TRUSTED_ORIGINS', '').strip()
    if _csrf_env:
        CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_env.split(',') if o.strip()]

    # Always include onrender.com wildcard so any subdomain is trusted
    if not any('onrender.com' in o for o in CSRF_TRUSTED_ORIGINS):
        CSRF_TRUSTED_ORIGINS.append('https://*.onrender.com')
