from django.views.generic import ListView

from accounts.mixins import RoleRequiredMixin

from .models import AuditLog


class AuditLogListView(RoleRequiredMixin, ListView):
    template_name = "audit/auditlog_list.html"
    context_object_name = "audit_entries"
    allowed_roles = ["chef"]

    def get_queryset(self):
        return AuditLog.objects.filter(department=self.request.user.department)
