from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp",
        "username",
        "action",
        "department",
        "document_title",
        "ip_address",
    ]
    list_filter = ["action", "department"]
    search_fields = ["username", "document_title"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
