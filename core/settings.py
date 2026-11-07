"""
Configuración del proyecto Django 'core'.
Sistema de Gestión - Mudanzas y Fletes Salta (Grupo 5).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Salen del .env (ver .env.example). Sin .env quedan los valores de desarrollo.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or 'django-insecure-cambia-esta-clave-en-produccion'

DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',') if h.strip()]

# Mapa del recorrido (OpenRouteService). Sin clave, las pantallas muestran solo el enlace «Cómo llegar».
ORS_API_KEY = os.environ.get('ORS_API_KEY', '').strip()


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'vehiculos',
    'usuarios',
    'pedidos',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'usuarios.auditoria.AuditoriaMiddleware',  # quién modifica, para LOG_AUDITORIA
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

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
                'usuarios.context_processors.seguridad',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'mudanzas_db'),
        'USER': os.environ.get('DB_USER', 'mudanzas_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'mudanzas_pass'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Salta'
USE_I18N = True
USE_TZ = True


STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


from django.contrib.messages import constants as messages_constants

# Claves con PBKDF2 (el de Django). En las pruebas se usa uno rápido para no esperar en cada usuario.
import sys
if 'test' in sys.argv:
    PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

MESSAGE_TAGS = {
    messages_constants.ERROR: 'danger',
}
