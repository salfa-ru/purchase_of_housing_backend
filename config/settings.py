import os

from dotenv import load_dotenv

load_dotenv()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SECRET_KEY = os.getenv('SECRET_KEY', 'default_key')

DEBUG = os.getenv('DEBUG', 'False') == 'True'
# пусть на сервере всегда работает postgres!
# 1 версия - не сработало:
# USE_SQLITE = os.getenv('USE_SQLITE', 'False') == 'True'

# 2 версия: (база работает, CORS а Ани не работает!)
# USE_SQLITE = os.getenv('USE_SQLITE', 'True').lower() in ('true', '1', 'yes')

DOMAIN = os.getenv('DOMAIN')

ALLOWED_HOSTS = [DOMAIN, os.getenv('HOST_IP'), 'localhost']


CSRF_TRUSTED_ORIGINS = [
    f'http://{DOMAIN}',
    f'https://{DOMAIN}',
    # 'http://*',
    # 'https://*',
]

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
    'rest_framework.authtoken',
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
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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


# if USE_SQLITE:
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
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
            'PORT': os.getenv('DB_PORT', 5432)
        }
    }

# DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': os.getenv('POSTGRES_DB', 'django'),
#             'USER': os.getenv('POSTGRES_USER', 'django'),
#             'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
#             'HOST': os.getenv('DB_HOST', ''),
#             'PORT': os.getenv('DB_PORT', 5432)
#         }
#     }

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
]


LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Старые настройки, когда не работала Аутентификация при выключенном DEBUG
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.backends.CustomAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

if DEBUG:
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].append(
        'rest_framework.authentication.TokenAuthentication'
    )

# Предлагаемые настройки, чтобы аутентификация работала с выключенным DEBUG
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'users.backends.CustomAuthentication',
#         'rest_framework.authentication.TokenAuthentication',
#     ],
#     'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
# }
# Стоит проверить, все ли тут работает


SPECTACULAR_SETTINGS = {
    'TITLE': 'purchase_of_housing_backend',
    'DESCRIPTION': 'Документация для приложения purchase_of_housing_backend',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# Настройки Django Q2 для деактивации устаревших объявлений
Q_CLUSTER = {
    'name': 'DjangoORM',
    'orm': 'default',  # Use the default Django database for task management
    'workers': 4,  # Number of workers to handle tasks
    'retry': 360,  # Time to keep retrying tasks before marking as failed
    'timeout': 60,  # Task execution timeout in seconds
    'queue_limit': 50,  # Max number of tasks in the queue
    'bulk': 10,  # Max number of tasks processed at once
    'catch_up': False,  # Prevent overdue tasks from being executed if the system was offline
    # 'admin': False,  # Hide Django Q models from the admin ( better try with admin.py, to see only as admin )
    'poll': 1,  # Poll every 1 second instead of 0.2
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://estate.ktsf.ru",
    "https://front.test.estate.ktsf.ru",
]

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

