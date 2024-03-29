"""
    Django settings for SmartServe project.

    Partially generated by "django-admin startproject" using Django 4.2.1.
"""

from copy import copy
from pathlib import Path
from typing import Any, Iterable, Sequence

from django.core.exceptions import ImproperlyConfigured
from environ import Env


BASE_DIR = Path(__file__).resolve().parent.parent  # NOTE: Build paths inside the project like this: BASE_DIR / "subdir"


Env.read_env(BASE_DIR / ".env")
env: Env = Env(
    PRODUCTION=(bool, True),
    PASSWORD_SIMILARITY_TO_USER_ATTRIBUTES=(float, 0.627),
    AUTH_TOKEN_MINIMUM_REFRESH_INTERVAL=(float, 300),
    API_RESPONSE_PAGINATION_SIZE=(int, 50),
    TEST_DATA_JSON_FILE_PATH=(str, None)
)


# Production Vs Development settings

if env("PRODUCTION"):
    prod_env: Env = Env(
        ALLOWED_HOSTS=(list, ["smartserve"]),
        ALLOWED_ORIGINS=(list, ["https://smartserve.com"]),
        LOG_LEVEL=(str, "WARNING")
    )

    log_level: str = prod_env("LOG_LEVEL").upper()

    DEBUG = False  # NOTE: Security Warning - Don't run with debug turned on in production!

    ALLOWED_HOSTS = prod_env("ALLOWED_HOSTS")
    ALLOWED_ORIGINS = prod_env("ALLOWED_ORIGINS")
    CSRF_TRUSTED_ORIGINS = copy(ALLOWED_ORIGINS)
else:
    dev_env: Env = Env(
        DEBUG=(bool, True),
        ALLOWED_HOSTS=(list, ["localhost"]),
        LOG_LEVEL=(str, "INFO")
    )

    log_level = dev_env("LOG_LEVEL").upper()

    DEBUG = dev_env("DEBUG")

    ALLOWED_HOSTS = dev_env("ALLOWED_HOSTS")


if not 0.1 <= env("PASSWORD_SIMILARITY_TO_USER_ATTRIBUTES") <= 1.0:
    raise ImproperlyConfigured("PASSWORD_SIMILARITY_TO_USER_ATTRIBUTES must be a float between 0.1 and 1.0.")

if not 1.0 <= env("AUTH_TOKEN_MINIMUM_REFRESH_INTERVAL"):
    raise ImproperlyConfigured("PASSWORD_SIMILARITY_TO_USER_ATTRIBUTES must be a float greater than or equal to 1.0")

if not env("API_RESPONSE_PAGINATION_SIZE") > 0:
    raise ImproperlyConfigured("API_RESPONSE_PAGINATION_SIZE must be an integer greater than 0.")

log_level_choices: Sequence[str] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
if log_level not in log_level_choices:
    raise ImproperlyConfigured(f"""LOG_LEVEL must be one of {",".join(f'"{log_level_choice}"' for log_level_choice in log_level_choices[:-1])} or \"{log_level_choices[-1]}\".""")


# Django REST Framework settings

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_AUTHENTICATION_CLASSES": ["knox.auth.TokenAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "PAGE_SIZE": env("API_RESPONSE_PAGINATION_SIZE")
}
REST_KNOX = {
    "AUTO_REFRESH": True,
    "MIN_REFRESH_INTERVAL": env("AUTH_TOKEN_MINIMUM_REFRESH_INTERVAL")
}


# Tests settings

TEST_DATA_JSON_FILE_PATH = Path(env("TEST_DATA_JSON_FILE_PATH")) if env("TEST_DATA_JSON_FILE_PATH") else None


# Logging settings

# noinspection SpellCheckingInspection
LOGGING = {
    "version": 1,
    "formatters": {
        "smartserve": {
            "format": "{levelname} - {module}: {message}",
            "style": "{"
        },
        "web_server": {
            "format": "[{asctime}] {message}",
            "datefmt": "%d/%b/%Y %H:%M:%S",
            "style": "{"
        }
    },
    "handlers": {
        "smartserve": {
            "class": "logging.StreamHandler",
            "formatter": "smartserve"
        },
        "web_server": {
            "class": "logging.StreamHandler",
            "formatter": "web_server"
        }
    },
    "loggers": {
        "django.server": {"handlers": ["web_server"], "level": log_level}
    },
    "root": {"handlers": ["smartserve"], "level": log_level}
}


# Web Server settings

WSGI_APPLICATION = "core.wsgi.application"
ROOT_URLCONF = "core.urls"
SECRET_KEY = env("SECRET_KEY")  # NOTE: Security Warning - The secret key is used for important secret stuff (keep the one used in production a secret!)
# noinspection PyUnresolvedReferences
STATIC_ROOT = "staticfiles/"
STATIC_URL = "static/"
MEDIA_ROOT = "media/"
MEDIA_URL = "media/"
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True


# Application Definition

# noinspection SpellCheckingInspection
INSTALLED_APPS = [
    "smartserve",
    "django.contrib.admindocs",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rangefilter",
    "rest_framework",
    "knox"
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware"
]


# Template settings

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages"
            ]
        }
    }
]


# Database settings

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3"
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Authentication settings

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {
            "user_attributes": ("username", "first_name", "last_name"),
            "max_similarity": env("PASSWORD_SIMILARITY_TO_USER_ATTRIBUTES")
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
AUTH_USER_MODEL = "smartserve.User"


# Internationalization, Language & Time settings

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True
