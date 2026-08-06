from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from .models import AuditLog
from .services import log_action


@receiver(user_logged_in)
def handle_user_logged_in(sender, request, user, **kwargs):
    log_action(AuditLog.Action.LOGIN_SUCCESS, user=user, request=request)


@receiver(user_logged_out)
def handle_user_logged_out(sender, request, user, **kwargs):
    log_action(AuditLog.Action.LOGOUT, user=user, request=request)


@receiver(user_login_failed)
def handle_user_login_failed(sender, credentials, request=None, **kwargs):
    log_action(
        AuditLog.Action.LOGIN_FAILED,
        request=request,
        username=credentials.get("username", ""),
    )
