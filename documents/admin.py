from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "department",
        "category",
        "uploaded_by",
        "uploaded_at",
        "is_active",
    ]
    list_filter = ["department", "category", "is_active"]
    search_fields = ["title"]
    date_hierarchy = "uploaded_at"

    def has_delete_permission(self, request, obj=None):
        return False
