import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

SECRET_KEY = os.getenv('SECRET_KEY', 'default_key')

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Документация API (Swagger/Redoc/schema): открыта всем на не-проде, на проде —
# только админам. Прод и тест крутятся на одном коде с DEBUG=False, поэтому
# значение берётся из окружения, а DEBUG остаётся лишь запасным вариантом.
DOCS_PUBLIC = os.getenv('DOCS_PUBLIC', str(DEBUG)).lower() == 'true'

# DOMAIN = os.getenv('DOMAIN')
# ALLOWED_HOSTS = [DOMAIN, os.getenv('HOST_IP'), 'localhost', 'api.prod.estate.ktsf.ru']


ALLOWED_HOSTS = [
    # os.getenv("DOMAIN"),
    # os.getenv("HOST_IP"),
    'localhost',
    '127.0.0.1',
    'api.test.estate.ktsf.ru',
    'api.prod.estate.ktsf.ru',
    '194.87.140.150',
]

extra_hosts = os.getenv('EXTRA_ALLOWED_HOSTS')

if extra_hosts:
    ALLOWED_HOSTS += [host.strip() for host in extra_hosts.split(',')]

RENDER_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')

if RENDER_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    # f'http://{DOMAIN}',
    # f'https://{DOMAIN}',
    # This is not right
    # "https://api.prod.estate.ktsf.ru",
    # "https://api.test.estate.ktsf.ru",
    # 'http://*',
    # 'https://*',
    'https://localhost',
    'https://127.0.0.1',
    'http://localhost:5173',
    'https://localhost:5173',
    'http://127.0.0.1:5173',
    'https://127.0.0.1:5173',
    'https://api.test.estate.ktsf.ru',
    'https://api.prod.estate.ktsf.ru',
]

extra_trusted_origins = os.getenv('EXTRA_CSRF_TRUSTED_ORIGINS')

if extra_trusted_origins:
    CSRF_TRUSTED_ORIGINS += [host.strip() for host in extra_trusted_origins.split(',')]

if RENDER_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_HOSTNAME}')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_spectacular',
    'django_filters',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_q',
    'corsheaders',
    'complaints.apps.ComplaintsConfig',
    'chats.apps.ChatsConfig',
    'notifications.apps.NotificationsConfig',
    'questions.apps.QuestionsConfig',
    'realty.apps.RealtyConfig',
    'realty_addresses.apps.RealtyAddressesConfig',
    'realty_displays.apps.RealtyDisplaysConfig',
    'realty_photos.apps.RealtyPhotosConfig',
    'realty_specificities.apps.RealtySpecificitiesConfig',
    'realty_values.apps.RealtyValuesConfig',
    'users.apps.UsersConfig',
    'djoser',
    'favorites',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

USE_SQLITE = os.getenv('USE_SQLITE', 'False').lower() in ('true', '1', 'yes')

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(DATA_DIR, 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'django'),
            'USER': os.getenv('POSTGRES_USER', 'django'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', ''),
            'PORT': os.getenv('DB_PORT', 5432),
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '60')),
            'CONN_HEALTH_CHECKS': True,
            'OPTIONS': {'sslmode': os.getenv('DB_SSLMODE', 'prefer')},
        }
    }

AUTH_USER_MODEL = 'users.User'

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
    {
        'NAME': 'users.validators.LetterAndDigitPasswordValidator',
    },
    {
        'NAME': 'users.validators.ContainsUppercaseValidator',
    },
    {
        'NAME': 'users.validators.MaximumLengthPasswordValidator',
        'OPTIONS': {'max_length': 60},
    },
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'

USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET')

if SUPABASE_BUCKET:
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': SUPABASE_BUCKET,
            'endpoint_url': os.getenv('SUPABASE_S3_ENDPOINT'),
            'access_key': os.getenv('SUPABASE_S3_ACCESS_KEY'),
            'secret_key': os.getenv('SUPABASE_S3_SECRET_KEY'),
            'region_name': os.getenv('SUPABASE_S3_REGION'),
            'addressing_style': 'path',
            'querystring_auth': False,
            'file_overwrite': False,
            'custom_domain': os.getenv('SUPABASE_PUBLIC_DOMAIN'),
        },
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Старые настройки, когда не работала Аутентификация при выключенном DEBUG
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'users.backends.CustomAuthentication',
#     ],
#     'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
# }
#
# if DEBUG:
#     REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].append(
#         'rest_framework.authentication.TokenAuthentication'
#     )


# НОВЫЕ Настройки, CORS должен работать в любом случае!

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'users.backends.CustomAuthentication',   # отключил, так как не пользуемся ИССОЙ!
        # 'rest_framework.authentication.TokenAuthentication',
        'users.authentication.CookieJWTAuthentication',
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'config.exceptions.db_error_exception_handler',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Недвижимость',
    'DESCRIPTION': 'Документация для приложения purchase_of_housing_backend',
    'VERSION': '1.0.1',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SERVE_AUTHENTICATION': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'SERVE_PERMISSIONS': (
        ['rest_framework.permissions.AllowAny']
        if DOCS_PUBLIC
        else ['rest_framework.permissions.IsAdminUser']
    ),
    'SWAGGER_UI_SETTINGS': {
        'defaultModelsExpandDepth': 0,
        'filter': True,
        'persistAuthorization': True,
        'displayRequestDuration': True,
        'docExpansion': 'none',
    },
    'SWAGGER_UI_OAUTH2': {
        'clientId': 'client',
        'clientSecret': 'secret',
        'realm': '',
        'appName': 'A-Недвижимость',
        'scopeSeparator': ' ',
        'additionalQueryStringParams': {},
    },
    # 🔧 ДОБАВЛЯЕМ ЭТО:
    'AUTHENTICATION_EXTENSIONS': [
        'config.swagger.BearerTokenScheme',
    ],
    'SECURITY': [
        {'BearerAuth': []},
    ],
}


# Настройки Django Q2 для деактивации устаревших объявлений
Q_CLUSTER = {
    'name': 'DjangoORM',
    'orm': 'default',  # Use the default Django database for task management
    'workers': int(os.getenv('Q_CLUSTER_WORKERS', '2')),
    'retry': 360,  # Time to keep retrying tasks before marking as failed
    'timeout': 60,  # Task execution timeout in seconds
    'queue_limit': 50,  # Max number of tasks in the queue
    'bulk': 10,  # Max number of tasks processed at once
    'catch_up': False,  # Prevent overdue tasks from being executed if the system was offline
    # 'admin': False,  # Hide Django Q models from the admin ( better try with admin.py, to see only as admin )
    'poll': 1,  # Poll every 1 second instead of 0.2
}

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'https://localhost:5173',
    'http://127.0.0.1:5173',
    'https://estate.ktsf.ru',
    'https://front.test.estate.ktsf.ru',
    'https://house-react-ten.vercel.app',
]

extra_cors_origins = os.getenv('EXTRA_CORS_ALLOWED_ORIGINS')

if extra_cors_origins:
    CORS_ALLOWED_ORIGINS += [origin.strip() for origin in extra_cors_origins.split(',')]

# REMOVE IN PRODUCTION
# CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_LOCALHOST = True

# ========== DJOSER ==========
DJOSER = {
    'USER_CREATE_PASSWORD_RETYPE': True,  # Требует re_password при регистрации
    'USER_EMAIL_REQUIRED': True,  # Email обязателен
    'SEND_ACTIVATION_EMAIL': False,  # Не отправляем письмо для активации
    'SET_PASSWORD_RETYPE': True,  # Подтверждение при смене пароля
    'PASSWORD_RESET_CONFIRM_RETYPE': True,  # Подтверждение при сбросе пароля
    'USERNAME_RESET_CONFIRM_RETYPE': True,  # Подтверждение при сбросе username
    'PASSWORD_RESET_CONFIRM_URL': 'api/password-reset/{uid}/{token}/',
    'PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND': True,
    'SERIALIZERS': {
        'user_create': 'users.serializers.UserCreateSerializer',
        'user': 'users.serializers.UserCreateSerializer',
        'current_user': 'users.serializers.CurrentUserSerializer',
    },
}

# URL для редиректа после сброса пароля
LOGIN_URL = 'api/auth/token-auth/'

SIMPLE_JWT = {
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60) if DEBUG else timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'JTI_CLAIM': 'jti',
    'REFRESH_COOKIE': 'refresh_token',
    'AUTH_COOKIE': 'access_token',
    # 🔧 ИСПРАВЛЯЕМ:
    'AUTH_COOKIE_SECURE': not DEBUG,  # True в продакшене (HTTPS), False локально (HTTP)
    'AUTH_COOKIE_HTTP_ONLY': True,  # Защита от XSS (всегда True)
    'AUTH_COOKIE_SAMESITE': 'None'
    if not DEBUG
    else 'Lax',  # Продакшен: None, локально: Lax
    'AUTH_COOKIE_PATH': '/',  # ✅ вместо /api/
}

# ========== EMAIL НАСТРОЙКИ (для сброса пароля) ==========
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # письма в консоль


# ========== НАСТРОЙКИ ДЛЯ HTTPS (через nginx) ==========
# Доверяем заголовки от nginx
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Используем заголовки от nginx для формирования URL
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
