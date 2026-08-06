"""
Settings shared by every environment (dev, prod, ...).

Environment-specific settings (DEBUG, ALLOWED_HOSTS, security headers, ...)
live in dev.py / prod.py, which import * from this module.
"""

from pathlib import Path

import environ

# dgh_intranet/settings/base.py -> dgh_intranet/settings -> dgh_intranet -> repo root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "documents",
    "audit",
    "core",
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

ROOT_URLCONF = "dgh_intranet.urls"

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
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "dgh_intranet.wsgi.application"
ASGI_APPLICATION = "dgh_intranet.asgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
#
# Plain field-by-field config (not a DATABASE_URL shortcut) so switching to
# PostgreSQL later is a matter of setting DB_ENGINE/DB_NAME/DB_USER/... in
# .env, not editing this file.

DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": env("DB_NAME", default=str(BASE_DIR / "db.sqlite3")),
        "USER": env("DB_USER", default=""),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default=""),
        "PORT": env("DB_PORT", default=""),
    }
}


# Custom user model — must exist before the first migration ever runs.
AUTH_USER_MODEL = "accounts.User"

# Auth
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/documents/"
LOGOUT_REDIRECT_URL = "/accounts/login/"


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
#
# Deliberate scope decision: this project is French-only. UI-facing text is
# written directly in French in templates/labels/verbose_name — no {% trans %}
# tags, no .po files, no LocaleMiddleware. Do not re-enable USE_I18N without
# revisiting that decision.

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (user uploads)
# Not wired into urls.py: downloads go through a permission-checked view,
# not direct media URLs.
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
