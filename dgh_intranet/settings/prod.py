"""
Production settings.

Status: configured, not deployed. Local development has used SQLite, and the
application and test suite have also been verified through Docker against
PostgreSQL. Docker currently starts Django's development server. A real
production deployment behind a production WSGI server, reverse proxy, and
TLS termination has not been performed. Production email delivery is also
unconfigured (dev.py uses a console email backend).
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
