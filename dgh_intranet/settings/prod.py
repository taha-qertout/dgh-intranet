"""
Production settings.

Status: configured, not deployed. These settings are written for a real
deployment but this project has, to date, only run via `manage.py runserver`
against SQLite in development. A real deployment additionally needs, at
minimum: a WSGI server (e.g. gunicorn) in front of Django, TLS termination
(e.g. via a reverse proxy or load balancer), PostgreSQL instead of SQLite,
and a real email backend (base.py/dev.py currently only console-print
emails via dev.py's EMAIL_BACKEND). None of that is provisioned here.
"""

from .base import *  # noqa: F401,F403
from .base import env

# Hardcoded, not env-driven: a prod settings file should never be able to
# turn DEBUG on by accident via a stray .env value.
DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Security hardening — only meaningful once served over HTTPS.
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Only correct behind a proxy that actually strips/sets this header itself
# (e.g. a load balancer terminating TLS and setting X-Forwarded-Proto).
# If the app is ever exposed directly, or behind a proxy that passes this
# header through from the client unmodified, this makes SECURE_SSL_REDIRECT
# trivially spoofable — the client could just send the header itself and
# Django would treat the request as secure when it isn't.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Explicit rather than relying on Django's global defaults, so this stays
# true even if those defaults ever change.
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
