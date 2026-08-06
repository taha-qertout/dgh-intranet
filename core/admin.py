from django.contrib import admin

from .models import Announcement, Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "department", "posted_by", "published_at", "is_active"]
    list_filter = ["department", "is_active"]
    search_fields = ["title"]
