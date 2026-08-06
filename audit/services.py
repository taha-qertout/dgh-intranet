import logging

from .models import AuditLog

logger = logging.getLogger(__name__)


def log_action(action, user=None, document=None, request=None, username=None):
    """Single entry point for writing audit entries.

    `username` is an explicit override for callers that have an attempted
    username but no User instance — namely the user_login_failed signal,
    which only provides submitted credentials, not a resolved user. When
    given, it wins over deriving the username from `user`.
    """
    resolved_user = user if user is not None and user.is_authenticated else None

    if username is not None:
        resolved_username = username
    elif resolved_user is not None:
        resolved_username = resolved_user.username
    else:
        resolved_username = ""

    if document is not None:
        department = document.department
    elif resolved_user is not None and resolved_user.department:
        department = resolved_user.department
    else:
        department = None

    document_title = document.title if document is not None else ""

    ip_address = None
    if request is not None:
        # request.META["REMOTE_ADDR"] only. Do NOT trust X-Forwarded-For
        # here — a real deployment behind a reverse proxy would need
        # explicit, configured trusted-proxy handling before reading that
        # header safely (it's client-controlled otherwise).
        ip_address = request.META.get("REMOTE_ADDR")

    try:
        return AuditLog.objects.create(
            action=action,
            user=resolved_user,
            username=resolved_username,
            department=department,
            document=document,
            document_title=document_title,
            ip_address=ip_address,
        )
    except Exception:
        logger.exception("Failed to write audit log entry (action=%s)", action)
        return None
