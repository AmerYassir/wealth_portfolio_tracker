"""Django settings for the Wealth Portfolio Tracker.

All environment-specific values come from env vars (see .env.base / .env.dev /
.env.prod). No secrets are hardcoded.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(name, default=None, cast=None):
    raw = os.environ.get(name, default)
    if raw is None:
        return None
    if cast is bool:
        return str(raw).lower() in ("1", "true", "yes", "on")
    if cast is not None:
        return cast(raw)
    return raw


SECRET_KEY = _env("SECRET_KEY", "insecure-dev-key")
DEBUG = _env("DEBUG", "False", cast=bool)
ALLOWED_HOSTS = [
    h.strip() for h in _env("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()
]

import sys as _sys  # noqa: E402
if "test" in _sys.argv:
    if "testserver" not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append("testserver")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "core",
    "agent",
    'audit',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _env("DB_NAME", "wealth"),
        "USER": _env("DB_USER", "wealth"),
        "PASSWORD": _env("DB_PASSWORD", ""),
        "HOST": _env("DB_HOST", "db"),
        "PORT": _env("DB_PORT", "5432"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": _env("REDIS_URL", "redis://redis:6379/0"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- DRF / JWT --------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

from datetime import timedelta as _td  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": _td(minutes=60),
    "REFRESH_TOKEN_LIFETIME": _td(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}
# --- django-ag-ui ------------------------------------------------------------
# Provider: OpenAI GPT via the [openai] extra. Model string uses Pydantic-AI's
# provider:model syntax. Swap the provider extra + MODEL together if changing.
DJANGO_AG_UI = {
    "MODEL": "openai:openai/gpt-oss-120b",
    "API_KEY": _env("OPENAI_API_KEY", None),
    "MODEL_SETTINGS": {"temperature": 0.1},
    "RETRIES": 2,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django_ag_ui": {"handlers": ["console"], "level": "DEBUG"},
        "pydantic_ai": {"handlers": ["console"], "level": "DEBUG"},
    },
}