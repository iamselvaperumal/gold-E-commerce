from pathlib import Path
from datetime import timedelta
# import dj_database_url
# from decouple import config

import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-secret-key")

# DEBUG = True
DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin', 
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'corsheaders',
    'accounts',
    'cloudinary',           # இதை add பண்ணு
    'cloudinary_storage',   
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ ADD - static files fix
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bitbyte_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'bitbyte_backend.wsgi.application'

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'bitbyte_db',
#         'USER': 'postgres',
#         'PASSWORD': 'Senthil@2003',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# DATABASES = {
#     'default': dj_database_url.config(
#         default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",  # ✅ இப்படி மாத்து
#         conn_max_age=600,
#         conn_health_checks=True,
#     )
# }

AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    'DEFAULT_FILTER_BACKENDS': [             # ← இந்த 4 lines add
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOW_ALL_ORIGINS = True

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Cloudinary Settings
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}


# razonpay
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_T0JMJzijqftP5f")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "CLm5lolSo1tLgZYh9fcwii5C")

MEDIA_URL = '/media/'
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Customer-only voice product search. Audio is saved only as a temporary file per request.
VOICE_SEARCH_ENABLED = os.environ.get("VOICE_SEARCH_ENABLED", "False").lower() in {"1", "true", "yes", "on"}
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")
VOICE_MAX_FILE_SIZE_MB = int(os.environ.get("VOICE_MAX_FILE_SIZE_MB", "10"))
VOICE_MAX_DURATION_SECONDS = int(os.environ.get("VOICE_MAX_DURATION_SECONDS", "30"))
VOICE_DEFAULT_LANGUAGE = os.environ.get("VOICE_DEFAULT_LANGUAGE", "ta")
VOICE_SUPPORTED_LANGUAGES = [item.strip() for item in os.environ.get("VOICE_SUPPORTED_LANGUAGES", "ta,en").split(",") if item.strip()]
VOICE_TRANSLATE_TO_ENGLISH = os.environ.get("VOICE_TRANSLATE_TO_ENGLISH", "False").lower() in {"1", "true", "yes", "on"}
VOICE_MIN_INTENT_CONFIDENCE = float(os.environ.get("VOICE_MIN_INTENT_CONFIDENCE", "0.60"))
VOICE_WEIGHT_TOLERANCE_GRAMS = float(os.environ.get("VOICE_WEIGHT_TOLERANCE_GRAMS", "0.5"))
VOICE_RESULT_LIMIT = int(os.environ.get("VOICE_RESULT_LIMIT", "20"))
