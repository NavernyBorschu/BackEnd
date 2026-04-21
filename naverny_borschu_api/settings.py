"""
Налаштування Django для проєкту Naverny Borschu API.

Цей файл містить основні конфігурації: додатки, middleware, шаблони,
бази даних, статичні файли тощо.
"""

import os
from datetime import timedelta
from pathlib import Path

# Базова директорія проєкту
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретний ключ для криптографічних операцій
SECRET_KEY = 'django-insecure-change-this-in-production'

DEBUG = False

# Дозволені хости (у production додати реальні домени)
ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# Додатки проєкту
INSTALLED_APPS = [
    'django.contrib.admin',      # Адмін-панель
    'django.contrib.auth',       # Авторизація
    'django.contrib.contenttypes', # Робота з типами контенту
    'django.contrib.sessions',   # Сесії
    'django.contrib.messages',   # Повідомлення
    'django.contrib.staticfiles', # Статичні файли
    
    # Сторонні додатки
    'rest_framework',           # Django REST Framework
    'rest_framework_simplejwt.token_blacklist',

    # Локальні додатки
    'core',                     # Основний API додаток
]

# Middleware обробники запитів
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Головний URL конфіг
ROOT_URLCONF = 'naverny_borschu_api.urls'

# Шаблони (templates)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Додати шляхи до шаблонів за потреби
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

# WSGI додаток
WSGI_APPLICATION = 'naverny_borschu_api.wsgi.application'


# Бази даних (PostgreSQL)
# За потреби значення можна перевизначити змінними середовища:
# DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'navernyborshchu'),
        'USER': os.getenv('DB_USER', 'borshchu_admin'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'NaVerNy-B0rsch-2026!'),
        'HOST': os.getenv('DB_HOST', 'navernyborshchu.com'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}


# Валідація паролів
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Інтернаціоналізація
LANGUAGE_CODE = 'uk'  # Українська мова за замовчуванням
TIME_ZONE = 'Europe/Kyiv'  # Київський час
USE_I18N = True
USE_TZ = True

# Шляхи до файлів перекладу
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Доступні мови
LANGUAGES = [
    ('uk', 'Українська'),
    ('en', 'English'),
]


# Статичні файли (CSS, JS, images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Директива для збору статичних файлів

# Медіа файли (завантаження користувачів)
# MEDIA_ROOT та MEDIA_URL для завантаження фото борщів; поки що використовується
# тривіальне зберігання у локальній директорії media/
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Тип первинного ключа за замовчуванням
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Налаштування Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',  # Тільки JSON відповіді
        'rest_framework.renderers.BrowsableAPIRenderer',  # Веб-інтерфейс API (для розробки)
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,  # Кількість записів на сторінку
}

# JWT (access / refresh). Refresh зберігається у БД (blacklist) при ротації.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Google Sign-In: один або кілька OAuth 2.0 Client ID (Web / iOS / Android), через кому.
# Приклад: GOOGLE_OAUTH_CLIENT_IDS=xxx.apps.googleusercontent.com,yyy.apps.googleusercontent.com
_raw_google_ids = os.getenv(
    'GOOGLE_OAUTH_CLIENT_IDS',
    os.getenv('GOOGLE_OAUTH_CLIENT_ID', ''),
)
GOOGLE_OAUTH_CLIENT_IDS = [x.strip() for x in _raw_google_ids.split(',') if x.strip()]
