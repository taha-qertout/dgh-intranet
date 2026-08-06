from .base import *  # noqa: F401,F403
from .base import env

DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Dev only: print outgoing email to the console instead of sending it.
# Prod needs a real backend — a documented future decision, not this one.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
