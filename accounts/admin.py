from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + ("department", "role")
    list_filter = ["role", "department", "is_staff"]
    search_fields = ["username", "email"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Informations DGH", {"fields": ("department", "role")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Informations DGH", {"fields": ("department", "role")}),
    )


admin.site.register(User, UserAdmin)
