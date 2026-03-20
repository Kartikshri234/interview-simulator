"""
Django Settings — AI Interview Simulator
"""
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ─────────────────────────────────────────────────
SECRET_KEY    = os.getenv('SECRET_KEY', 'django-insecure-replace-this-key')
DEBUG         = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

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
    'rest_framework_simplejwt.token_blacklist',   # ← token blacklist
    'corsheaders',
    'channels',
    # Local
    'apps.users',
    'apps.interview',
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

# ── Database ─────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── Auth ─────────────────────────────────────────────────────
AUTH_USER_MODEL = 'users.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# ── REST Framework ───────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Global throttle — additional per-view throttles applied in api_views.py
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '120/minute',
        'token_obtain': '5/minute',    # applied explicitly on login view
        'token_refresh': '10/minute',  # applied explicitly on refresh view
    },
}

# ── JWT — hardened config ────────────────────────────────────
SIMPLE_JWT = {
    # Token lifetimes
    'ACCESS_TOKEN_LIFETIME':  timedelta(minutes=30),   # short-lived
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # Rotation & blacklisting
    'ROTATE_REFRESH_TOKENS':   True,   # issue a new refresh token on every refresh
    'BLACKLIST_AFTER_ROTATION': True,  # old refresh token is immediately blacklisted

    # Algorithm & signing
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,

    # Token type enforcement
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME':  'HTTP_AUTHORIZATION',
    'USER_ID_FIELD':     'id',
    'USER_ID_CLAIM':     'user_id',

    # Use our custom token class that embeds extra claims
    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.jwt_utils.CustomTokenObtainPairSerializer',

    # Prevent token reuse after single use (access tokens only)
    'UPDATE_LAST_LOGIN': True,

    # Token classes
    'ACCESS_TOKEN_CLASS':  'rest_framework_simplejwt.tokens.AccessToken',
    'REFRESH_TOKEN_CLASS': 'rest_framework_simplejwt.tokens.RefreshToken',
    'SLIDING_TOKEN_CLASS': 'rest_framework_simplejwt.tokens.SlidingToken',
    'SLIDING_TOKEN_REFRESH_CLASS': 'rest_framework_simplejwt.tokens.SlidingToken',

    'SLIDING_TOKEN_LIFETIME':         timedelta(minutes=30),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),

    # JTI claim used for blacklisting
    'JTI_CLAIM': 'jti',
}

# ── CORS ─────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS   = ['http://localhost:8000', 'http://127.0.0.1:8000']
CORS_ALLOW_CREDENTIALS = True

# ── Static & Media ───────────────────────────────────────────
STATIC_URL       = '/static/'
STATIC_ROOT      = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Channel Layers ───────────────────────────────────────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [os.getenv('REDIS_URL', 'redis://localhost:6379')]},
    },
}

# ── AI APIs ──────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# ── i18n ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
