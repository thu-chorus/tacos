from django.contrib import admin

from .models import SystemAnnouncement


@admin.register(SystemAnnouncement)
class SystemAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("id", "publish_time", "title", "short_content", "created_at")
    list_filter = ("publish_time", "created_at")
    search_fields = ("title", "content")
    ordering = ("-publish_time", "-id")

    def short_content(self, obj):  # type: ignore[override]
        return (obj.content or "")[:50]

    short_content.short_description = "内容"
